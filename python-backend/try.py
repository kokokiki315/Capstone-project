from ultralytics import YOLO
import datetime, os,cv2, time ,requests, json, base64, asyncio, mysql.connector
import numpy as np

model = YOLO(r"C:\Users\jy\Desktop\Capstone project\runs\detect\train_dataset_finetune\weights\best.pt")
cam = cv2.VideoCapture(0)
cam.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
width=int(cam.get(cv2.CAP_PROP_FRAME_WIDTH))
height=int(cam.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = cam.get(cv2.CAP_PROP_FPS)
font = cv2.FONT_HERSHEY_DUPLEX
videoName=datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S") #https://www.geeksforgeeks.org/python/display-date-and-time-in-videos-using-python-opencv/
roi = np.array([[100, int(height/2)],[width-100, int(height/2)],[width-100, height],[100, height]])
capturedframe = 0
writer = None
recording = False
capturecooldown=False
getVideoName=videoName
content = ""
os.makedirs("Frames", exist_ok=True)

mydb = mysql.connector.connect(
  host="localhost",
  user="root",
  password="Kenstar1",
  database="detectrecord"
)

mycursor = mydb.cursor()

async def countdown(seconds):
    global capturecooldown 
    await asyncio.sleep(seconds)
    capturecooldown = False

def storeevent(dt, filename, content):
    with mysql.connector.connect(
        host="localhost",
        user="root",
        password="Kenstar1",
        database="detectrecord"
    ) as mydb:
        cursor = mydb.cursor()
        sql = '''
        INSERT INTO events (timestamp, image_name, image_path, image_analysis)
        VALUES (%s, %s, %s, %s)
        '''
        cursor.execute(sql, (dt, filename, f"Frames/{filename}", content))
        mydb.commit()

#save the file name as current time
def videoWriter():
    # Video writer
    global writer
    writer=cv2.VideoWriter(videoName+'.mp4',
                                cv2.VideoWriter_fourcc(*"mp4v"),
                                10, (width, height))


def openCam():
    if cam.isOpened():
            return True
    else:
            print("No Camera Detected")
            return False
    
async def runCam():
    global capturedframe, writer, recording, capturecooldown, content
    # Process video
    while cam.isOpened():
        success, frame = cam.read()
        #https://docs.ultralytics.com/reference/engine/results/#ultralytics.engine.results.Boxes
        if not success:
            print("Frame Error")
            break
        #draw roi https://www.youtube.com/watch?v=tbscP_d11Zw
        cv2.polylines(frame, [roi], True, (255,255,0), 2)
        #https://docs.ultralytics.com/modes/track/#features-at-a-glance
        dt = str(datetime.datetime.now())

        #https://python.plainenglish.io/drawing-shapes-and-text-in-images-with-opencv-00a497c919e1
        cv2.putText(frame, dt,(10,30),           # Position (x, y)
                            font, 1,              # Font and scale
                            (0, 255, 0),        # Color (B, G, R)
                            2,                   # Thickness
                            cv2.LINE_8)          # Line type
        
        results = model.track(frame, conf=0.8, iou=0.5, persist=True)  # track the objects
        annotated_frame = results[0].plot()
        
        cv2.imshow('Camera' , annotated_frame)
        #https://docs.ultralytics.com/reference/engine/results/#ultralytics.engine.results.Boxes

        for box in results[0].boxes:
            cls_id = int(box.cls[0])
            cls_name = results[0].names[cls_id]

            # Screenshot for person
            if cls_name in ["person","car"]:
                if not capturecooldown:
                    filename = f"screenshot_{cls_name}{capturedframe}.jpg"
                    file_path = os.path.join("Frames", filename)
                    cv2.imwrite(file_path, frame)
                    print(f"Image Captured {filename}")
                    capturecooldown=True

                    # Run API call in background
                    asyncio.create_task(asyncio.to_thread(geminiApi, file_path))

                    # Start cooldown timer (non-blocking)
                    asyncio.create_task(countdown(10))
                    

            # Bottom-center of the bounding box
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            center_x = int((x1 + x2) / 2)
            center_y = y2
            cv2.circle(frame, (center_x, center_y), 5, (0,0,255), -1)

            inside_roi = cv2.pointPolygonTest(roi, (center_x, center_y), False) >= 0

            # Start or stop recording
            if cls_name == "person" and inside_roi:
                asyncio.create_task(startrecording(frame))
            else:
                if recording:
                    print("Person left ROI – stop recording")
                    writer.release()
                    recording = False

        if cv2.waitKey(1) & 0xFF == ord('s'):
            break

    if recording:
        writer.release()
    cam.release()
    cv2.destroyAllWindows()
    
def geminiApi(filename):
    global content
    api_key = os.getenv("OPENROUTER_API_KEY")

    with open(filename, "rb") as f:
        img_base64 = base64.b64encode(f.read()).decode("utf-8")

    image_data_url = f"data:image/jpeg;base64,{img_base64}"

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": "google/gemini-2.0-flash-exp:free",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Describe this CCTV image in detail:"},
                        {"type": "image_url", "image_url": {"url": image_data_url}},
                    ],
                }
            ],
        },
        timeout=60,
    )

    response_data = response.json()
    
    try:
        # Extract the model text
        content = response_data["choices"][0]["message"]["content"].strip()
        print(content)
        #save into database
        dt = str(datetime.datetime.now())
        storeevent(dt, os.path.basename(filename), content)
    except KeyError:
        print("Error: Unexpected response format")
        print(response_data)



def release():
    if writer:
        writer.release()
    cam.release()
    cv2.destroyAllWindows()
#https://github.com/ultralytics/ultralytics/blob/main/ultralytics/cfg/datasets/Objects365.yaml

async def startrecording(frame):
    global writer, recording
    if not recording:
        print("Person entered ROI – start recording")
        videoName = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        writer = cv2.VideoWriter(videoName+'.mp4',
                                cv2.VideoWriter_fourcc(*"mp4v"),
                                fps, (width, height))
        recording = True
    writer.write(frame)
    

async def main():
    if openCam():
        await runCam()

if __name__ == "__main__":
    asyncio.run(main())

