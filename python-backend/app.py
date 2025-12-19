from flask import Flask, Response, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import threading
import cv2
import time
import datetime
import os
import numpy as np
from ultralytics import YOLO
import paho.mqtt.client as mqtt
from dotenv import load_dotenv
from collections import deque
import json
from flask import send_from_directory
import mysql.connector
import tinytuya
import requests

try:
    from api import geminiApi
    from db import storeevent
except ImportError:
    def geminiApi(path): pass
    def storeevent(name, type): pass

load_dotenv()

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# ================= GLOBAL VARIABLES =================
outputFrame = None
latest_hq_frame = None
lock = threading.Lock()
mqtt_client = None
is_camera_running = True 
frame_buffer = deque(maxlen=1)

# Logic Variables
last_publish = {"person": 0.0, "car": 0.0}
last_capture_time = 0
last_person_seen_time = 0
capturedframe = 0
recording = False
writer = None
system_logs = deque(maxlen=100)  # Increased capacity

# Device tracking
devices = {
    "camera": {"online": True, "last_seen": time.time()},
    "mqtt": {"online": False, "last_seen": 0},
    "esp32": {"online": False, "last_seen": 0}
}

bulb_device_id = 'a34998c1f1ade9e273eovl'
bulb_ip = '192.168.100.45' 
bulb_local_key = 'QB-qEXZm*hc!PMxz'
bulb_version = 3.5

print("[SYSTEM] Connecting to Tuya Bulb...")
try:
    bulb = tinytuya.BulbDevice(bulb_device_id, bulb_ip, bulb_local_key)
    bulb.set_version(bulb_version)
    bulb.set_socketPersistent(True)
    print("[SYSTEM] Bulb Connected!")
except Exception as e:
    print(f"[ERROR] Bulb connection failed: {e}")
    bulb = None
# CONFIG
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR) 
MODEL_PATH = os.path.join(PROJECT_ROOT, "runs", "detect", "train_dataset_finetune", "weights", "best.pt")

CAM_INDEX = int(os.getenv("CAM_INDEX", 0))
PUBLISH_COOLDOWN = float(os.getenv("PUBLISH_COOLDOWN", 5.0))
GEMINI_INTERVAL = int(os.getenv("GEMINI_INTERVAL", 5))
RECORDING_PATIENCE = float(os.getenv("RECORDING_PATIENCE", 3.0))

# OPTIMIZATION CONFIG
STREAM_WIDTH = 640
STREAM_HEIGHT = 360
JPEG_QUALITY = 40  # Increased for better quality
DETECTION_SKIP = 5  # Process every 3rd frame (was 2)
frame_count = 0
TARGET_FPS = 30  # Target streaming FPS

# ================= HELPER FUNCTIONS =================
def add_log(event_type, message):
    """Add system log with timestamp and emit via WebSocket"""
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    log_entry = {
        "time": timestamp,
        "event": f"[{event_type}] {message}"
    }
    system_logs.append(log_entry)
    
    # Emit to connected WebSocket clients
    try:
        socketio.emit('new_log', log_entry)
    except:
        pass

def update_device_status(device_name, online=True):
    """Update device online status"""
    if device_name in devices:
        devices[device_name]["online"] = online
        devices[device_name]["last_seen"] = time.time()
        socketio.emit('device_update', {
            "device": device_name,
            "online": online,
            "timestamp": time.time()
        })

# ================= MQTT SETUP =================
def start_mqtt():
    global mqtt_client
    broker = os.getenv("MQTT_BROKER", "xxxxxx.s1.eu.hivemq.cloud")
    port = int(os.getenv("MQTT_PORT", 8883))
    user = os.getenv("MQTT_USER")
    pw = os.getenv("MQTT_PASS")

    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, "Flask_Backend_V2")
    if user and pw:
        mqtt_client.username_pw_set(user, pw)
    mqtt_client.tls_set()
    mqtt_client.tls_insecure_set(True)
    
    def on_connect(client, userdata, flags, reason_code, properties=None):
        if reason_code == 0:
            update_device_status("mqtt", True)
            add_log("MQTT", "Connected successfully")
            # Subscribe to status topics
            client.subscribe(os.getenv("MQTT_STATUS_TOPIC", "gate/status"))
        else:
            update_device_status("mqtt", False)
            add_log("MQTT", f"Connection failed: {reason_code}")
    
    def on_message(client, userdata, msg):
        """Handle incoming MQTT messages"""
        try:
            payload = msg.payload.decode()
            add_log("MQTT", f"Received: {payload}")
            
            # Update ESP32 status
            if "esp32" in payload.lower():
                update_device_status("esp32", True)
        except Exception as e:
            add_log("ERROR", f"MQTT message error: {e}")
    
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    
    try:
        mqtt_client.connect(broker, port)
        mqtt_client.loop_start()
    except Exception as e:
        update_device_status("mqtt", False)
        add_log("MQTT", f"Connection error: {e}")

# ================= PROCESS FUNCTIONS =================
def process_gemini_thread(file_path, frame):
    global bulb # Ensure we can access the bulb object
    
    try:
        cv2.imwrite(file_path, frame)
        
        # 1. Capture the returned text from Gemini
        analysis_result = geminiApi(file_path) 
        
        add_log("AI", f"Analyzed: {analysis_result}")
        
        # 2. VLM AUTOMATION LOGIC        
        if analysis_result:
            result_lower = analysis_result.lower()
            # Send the image + the AI description to your phone
            send_telegram_alert(f"📢 Analysis: {analysis_result}", file_path)
            light_triggered = False
            # Scenario: Delivery or Visitor -> Turn Light ON for convenience
            if "delivery" in result_lower or "visitor" in result_lower:
                print("[AI ACTION] Visitor detected. Welcoming light.")
                if bulb:
                    bulb.turn_on()
                    bulb.set_colour(255, 255, 0) 
                    light_triggered = True
                    
            # Scenario: Security Threat -> Turn Light RED (if supported) or ON "suspicious"
            elif "suspicious" in result_lower or "stealing" in result_lower:
                print("[AI ACTION] Threat detected! Turning light ON.")
                if bulb:
                    bulb.turn_on()
                    bulb.set_colour(255, 0, 0) 
                    light_triggered = True

            if light_triggered:
                # Start a separate thread to count 3 seconds without freezing the app
                threading.Thread(target=turn_off_light_after_delay, args=(3,)).start()
                
        # Emit event update via WebSocket (Keep existing code)
        socketio.emit('new_event', {
            "timestamp": datetime.datetime.now().isoformat(),
            "type": "ai_analysis",
            "image": os.path.basename(file_path),
            "analysis": analysis_result # Send the actual text to frontend
        })

    except Exception as e:
        add_log("ERROR", f"Gemini processing failed: {e}")

# ================= NOTIFICATION HELPER =================
def send_telegram_alert(message, image_path=None):
    """Sends a notification to your Telegram App"""
    try:
        # Load credentials from .env
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")

        if not bot_token or not chat_id:
            print("[WARN] Telegram credentials missing in .env")
            return

        # API Endpoint
        send_text_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

        # 1. Send Image (if available) with Caption
        if image_path and os.path.exists(image_path):
            send_photo_url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
            with open(image_path, "rb") as f:
                # Send photo with the AI description as the caption
                requests.post(send_photo_url, 
                              data={"chat_id": chat_id, "caption": message}, 
                              files={"photo": f})
        else:
            # 2. Fallback to Text Only
            requests.post(send_text_url, json={"chat_id": chat_id, "text": message})
        
        add_log("NOTIFY", "Telegram alert sent")

    except Exception as e:
        print(f"[ERROR] Failed to send notification: {e}")

# ================= LIGHT TIMER HELPER =================
def turn_off_light_after_delay(duration=2):
    """Waits for 'duration' seconds then turns the Tuya bulb OFF"""
    time.sleep(duration)
    if bulb:
        try:
            bulb.turn_off()
            add_log("LIGHT", f"Auto-turned OFF after {duration}s")
        except Exception as e:
            print(f"[ERROR] Failed to auto-turn off light: {e}")

# ================= CAMERA PROCESS =================
def camera_processing():
    global outputFrame, lock, mqtt_client, recording, writer, latest_hq_frame
    global last_publish, last_capture_time, last_person_seen_time, capturedframe
    global is_camera_running, frame_count, frame_buffer, bulb

    add_log("SYSTEM", "Initializing camera system...")
    print(f"[SYSTEM] Loading Model: {MODEL_PATH}")
    
    # Load model to GPU
    try:
        model = YOLO(MODEL_PATH).to('cuda')
    except Exception as e:
        print(f"[ERROR] Failed to load model to CUDA: {e}")
        model = YOLO(MODEL_PATH) # Fallback to CPU

    cam = None
    
    # Ensure Recordings directory exists
    rec_dir = os.path.join(PROJECT_ROOT, "Recordings")
    if not os.path.exists(rec_dir):
        os.makedirs(rec_dir)

    # Ensure Frames directory exists
    if not os.path.exists("Frames"):
        os.makedirs("Frames")

    add_log("SYSTEM", "Camera system ready")

    # Variables for logic
    font = cv2.FONT_HERSHEY_DUPLEX
    
    # We will read these from the first actual frame to be safe
    real_width = None
    real_height = None

    # --- NEW: Scheduler Flag ---
    light_auto_turned_on = False

    try:
        while True:
            if not is_camera_running:
                if cam is not None:
                    cam.release()
                    cam = None
                    update_device_status("camera", False)
                
                # Show offline screen
                with lock:
                    blank = np.zeros((360, 640, 3), np.uint8) # Default stream size
                    cv2.putText(blank, "CAMERA OFFLINE", (150, 180), font, 1, (255,255,255), 2)
                    outputFrame = blank
                time.sleep(0.5)
                continue

            if cam is None:
                cam = cv2.VideoCapture(CAM_INDEX)
                cam.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                cam.set(cv2.CAP_PROP_FPS, 30)
                update_device_status("camera", True)
                add_log("CAMERA", "Camera connected")

            success, frame = cam.read()
            if not success:
                print("[ERROR] Failed to read frame")
                time.sleep(0.1)
                continue

            # --- DYNAMIC RESOLUTION FIX ---
            if real_width is None:
                real_height, real_width = frame.shape[:2]
                print(f"[SYSTEM] Real Camera Resolution: {real_width}x{real_height}")
                
                # Define ROI based on REAL dimensions
                roi = np.array([
                    [100, int(real_height * 0.70)],
                    [real_width - 100, int(real_height * 0.70)],
                    [real_width - 100, real_height],
                    [100, real_height]
                ])

            clean_frame = frame.copy()
            current_time = time.time()
            
            with lock:
                latest_hq_frame = clean_frame.copy()

            # 1. NEW FEATURE: AUTO LIGHT AT 7 PM (19:00)
            current_hour = datetime.datetime.now().hour
            
            if current_hour == 18 and not light_auto_turned_on:
                print("[SCHEDULE] It's 7 PM. Turning light ON.")
                if bulb:
                    try:
                        bulb.turn_on()
                        light_auto_turned_on = True # Lock so we don't spam
                        add_log("SCHEDULE", "Auto-turned light ON (7 PM)")
                    except Exception as e:
                        print(f"[ERROR] Schedule failed: {e}")
            
            # Reset flag at Midnight so it works tomorrow
            elif current_hour == 0:
                light_auto_turned_on = False

            # YOLO Tracking
            results = model.track(frame, conf=0.45, persist=True, verbose=False)
            annotated_frame = results[0].plot()

            # --- ROI & LOGIC ---
            person_in_roi = False
            detected_classes = []
            
            if results and len(results[0].boxes) > 0:
                for box in results[0].boxes:
                    cls_id = int(box.cls[0])
                    cls_name = results[0].names[cls_id]
                    detected_classes.append(cls_name)
                    
                    # ROI Check
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    center_point = ((x1+x2)//2, y2)
                    
                    if cls_name == "person":
                        if cv2.pointPolygonTest(roi, center_point, False) >= 0:
                            person_in_roi = True
                            last_person_seen_time = current_time

            # Draw ROI
            cv2.polylines(annotated_frame, [roi], True, (255, 255, 0), 2)
            cv2.putText(annotated_frame, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                       (10, 30), font, 0.8, (0, 255, 0), 2)

            # --- RECORDING LOGIC ---
            if person_in_roi and not recording:
                filename = datetime.datetime.now().strftime("REC_%Y-%m-%d_%H-%M-%S.mp4")
                filepath = os.path.join(rec_dir, filename)
                writer = cv2.VideoWriter(filepath, cv2.VideoWriter_fourcc(*'mp4v'), 25, (real_width, real_height))
                recording = True
                add_log("RECORD", f"Started: {filename}")
                socketio.emit('recording_status', {'recording': True})

            if recording:
                if writer is not None:
                    writer.write(annotated_frame)
                
                cv2.circle(annotated_frame, (30, 60), 10, (0, 0, 255), -1)
                cv2.putText(annotated_frame, "REC", (50, 65), font, 0.7, (0, 0, 255), 2)
                
                if not person_in_roi:
                    time_gone = current_time - last_person_seen_time
                    remaining = int(RECORDING_PATIENCE - time_gone)
                    cv2.putText(annotated_frame, f"Stop in: {remaining}s", (30, 90), font, 0.6, (0, 165, 255), 2)
                    
                    if time_gone > RECORDING_PATIENCE:
                        writer.release()
                        writer = None
                        recording = False
                        add_log("RECORD", "Recording saved")
                        socketio.emit('recording_status', {'recording': False})

            # --- WEBSOCKET STREAM OUTPUT ---
            small_frame = cv2.resize(annotated_frame, (STREAM_WIDTH, STREAM_HEIGHT))
            with lock:
                outputFrame = small_frame.copy()

            # --- MQTT LOGIC ---
            if mqtt_client:
                if "car" in detected_classes and (current_time - last_publish["car"] > PUBLISH_COOLDOWN):
                    mqtt_client.publish(os.getenv("MQTT_TOPIC"), "open_big")
                    last_publish["car"] = current_time
                    add_log("MQTT", "Sent: open_big")
                elif "person" in detected_classes and (current_time - last_publish["person"] > PUBLISH_COOLDOWN):
                    mqtt_client.publish(os.getenv("MQTT_TOPIC"), "scan_person")
                    last_publish["person"] = current_time
                    add_log("MQTT", "Sent: scan_person")

            # 2. NEW FEATURE: PERIODIC 30-MIN SCAN + MOTION SCAN
            elapsed_since_last_ai = current_time - last_capture_time
            
            # Trigger A: Motion (Person/Car) detected + Interval passed
            motion_trigger = any(t in detected_classes for t in ["person", "car"]) and (elapsed_since_last_ai >= GEMINI_INTERVAL)
            
            # Trigger B: 30 Minutes (1800s) passed without any check (Periodic Scan)
            periodic_trigger = elapsed_since_last_ai >= 1800 

            if motion_trigger or periodic_trigger:
                trigger_reason = "Motion" if motion_trigger else "Periodic Scan"
                
                capturedframe += 1
                # Save raw frame for AI analysis
                threading.Thread(target=process_gemini_thread, 
                               args=(f"Frames/{capturedframe}.jpg", clean_frame)).start()
                
                last_capture_time = current_time
                add_log("AI", f"Scan initiated by: {trigger_reason}")

    except Exception as e:
        print(f"[CRITICAL ERROR] Camera loop crashed: {e}")
    finally:
        if writer is not None:
            writer.release()
            print("[SYSTEM] Recording saved on exit.")
        if cam is not None:
            cam.release()

def save_snapshot_thread(file_path, frame):
    try:
        # Save file locally
        cv2.imwrite(file_path, frame)
        
        # SKIP Gemini API. Directly save to DB.
        filename = os.path.basename(file_path)
        static_analysis = "Manual Snapshot" # Static label for the dashboard
        
        storeevent(filename, static_analysis)
        
        add_log("CONTROL", f"Snapshot saved: {filename}")
        
        # Update Frontend immediately
        socketio.emit('new_event', {
            "timestamp": datetime.datetime.now().isoformat(),
            "type": "manual_capture",
            "image": filename,
            "analysis": static_analysis 
        })

    except Exception as e:
        add_log("ERROR", f"Snapshot failed: {e}")

# ================= FLASK ROUTES =================
@app.route('/api/on', methods=['POST'])
def turn_light_on():
    if bulb:
        try:
            bulb.turn_on()
            return jsonify({"status": "success", "message": "Light turned ON"})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500
    return jsonify({"status": "error", "message": "Bulb not connected"}), 500

@app.route('/api/off', methods=['POST'])
def turn_light_off():
    if bulb:
        try:
            bulb.turn_off()
            return jsonify({"status": "success", "message": "Light turned OFF"})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500
    return jsonify({"status": "error", "message": "Bulb not connected"}), 500

@app.route('/video_feed')
def video_feed():
    def generate():
        global outputFrame, lock
        
        # Create a black placeholder frame if camera is broken
        blank_frame = np.zeros((360, 640, 3), np.uint8)
        cv2.putText(blank_frame, "NO SIGNAL", (200, 180), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        while True:
            with lock:
                if outputFrame is None:
                    frame_to_encode = blank_frame
                else:
                    frame_to_encode = outputFrame

            # --- OPTIMIZATION 1: COMPRESSION ---
            # We explicitly use JPEG Quality 50 (defined globally) to reduce file size
            # This makes the stream much faster over Wi-Fi
            flag, encodedImage = cv2.imencode(".jpg", frame_to_encode, [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY])
            
            if not flag:
                continue

            yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + 
                  bytearray(encodedImage) + b'\r\n')
            
            # --- OPTIMIZATION 2: SYNC FPS ---
            # Sleep for 0.04s (approx 25 FPS) instead of 0.01s (100 FPS).
            # This prevents sending duplicate frames and saves network bandwidth.
            time.sleep(0.04)
            
    return Response(generate(), mimetype="multipart/x-mixed-replace; boundary=frame")

# ================= NEW ORGANIZED API ENDPOINTS =================

@app.route('/api/devices', methods=['GET'])
def get_devices():
    """Get all connected devices and their status"""
    device_list = []
    for name, info in devices.items():
        last_seen = info["last_seen"]
        if last_seen > 0:
            time_diff = time.time() - last_seen
            if time_diff < 60:
                last_seen_str = f"{int(time_diff)}s ago"
            elif time_diff < 3600:
                last_seen_str = f"{int(time_diff/60)}m ago"
            else:
                last_seen_str = f"{int(time_diff/3600)}h ago"
        else:
            last_seen_str = "Never"
            
        device_list.append({
            "name": name.upper(),
            "online": info["online"],
            "last_seen": last_seen_str,
            "type": "Camera" if name == "camera" else "Network Service"
        })
    
    return jsonify(device_list)


@app.route('/api/control', methods=['POST'])
def control_gate():
    data = request.json
    action = data.get('action')
    if mqtt_client:
        mqtt_client.publish(os.getenv("MQTT_TOPIC"), action)
        add_log("CONTROL", f"Manual trigger: {action}")
        return jsonify({"status": "success", "action": action})
    return jsonify({"status": "error", "message": "MQTT not connected"}), 500

@app.route('/api/camera/toggle', methods=['POST'])
def toggle_camera():
    global is_camera_running
    data = request.json
    is_camera_running = bool(data.get('state', not is_camera_running))
    add_log("CAMERA", f"Camera {'started' if is_camera_running else 'stopped'}")
    return jsonify({"state": is_camera_running})

@app.route('/api/camera/status', methods=['GET'])
def camera_status():
    return jsonify({"state": is_camera_running})

@app.route('/api/logs', methods=['GET'])
def get_logs():
    return jsonify(list(system_logs))

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "online",
        "camera": is_camera_running,
        "mqtt": mqtt_client is not None and devices["mqtt"]["online"],
        "recording": recording,
        "timestamp": datetime.datetime.now().isoformat()
    })
# --- ADD THIS NEW ROUTE TO SERVE IMAGES ---
@app.route('/frames/<path:filename>')
def serve_frames(filename):
    # This allows the frontend to access images in your 'Frames' folder
    return send_from_directory(os.path.join(PROJECT_ROOT, 'Frames'), filename)

# --- REPLACE THE EXISTING 'get_events' FUNCTION ---
@app.route('/api/events', methods=['GET'])
def get_events():
    """Fetch real event history from MySQL"""
    try:
        # Connect to your Database
        mydb = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Kenstar1",
            database="detectrecord"
        )
        cursor = mydb.cursor(dictionary=True) # dictionary=True makes accessing columns easier

        # Get last 20 events, newest first
        cursor.execute("SELECT * FROM events ORDER BY timestamp DESC LIMIT 20")
        rows = cursor.fetchall()
        
        events_data = []
        for row in rows:
            # Create a valid URL for the browser
            # We use 'image_name' from your DB to build the link
            image_url = f"{request.host_url}frames/{row['image_name']}"
            
            events_data.append({
                "id": row['id'],
                "timestamp": row['timestamp'].strftime("%Y-%m-%d %H:%M:%S"),
                "analysis": row['image_analysis'] or "No analysis available",
                "image_url": image_url
            })

        cursor.close()
        mydb.close()
        return jsonify(events_data)

    except Exception as e:
        print("DB Fetch Error:", e)
        return jsonify({"error": str(e)}), 500
    
@app.route('/api/capture', methods=['POST'])
def manual_capture():
    global latest_hq_frame, capturedframe
    
    if latest_hq_frame is None:
        return jsonify({"status": "error", "message": "Camera not ready"}), 503

    try:
        capturedframe += 1
        # timestamped filename
        filename = f"Frames/manual_{int(time.time())}.jpg"
        
        with lock:
            frame_to_process = latest_hq_frame.copy()

        # START THE FAST THREAD (No AI)
        threading.Thread(target=save_snapshot_thread, 
                         args=(filename, frame_to_process)).start()

        return jsonify({"status": "success", "message": "Snapshot taken"})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ================= WEBSOCKET HANDLERS =================

@socketio.on('connect')
def handle_connect():
    print('[WebSocket] Client connected')
    emit('connection_status', {'status': 'connected'})

@socketio.on('disconnect')
def handle_disconnect():
    print('[WebSocket] Client disconnected')

@socketio.on('request_logs')
def handle_log_request():
    emit('logs_update', list(system_logs))

# ================= STARTUP =================

if __name__ == '__main__':
    add_log("SYSTEM", "Starting Flask server...")
    start_mqtt()
    t = threading.Thread(target=camera_processing)
    t.daemon = True
    t.start()
    
    # Use SocketIO run instead of app.run
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)