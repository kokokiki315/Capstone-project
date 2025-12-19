#include <Arduino.h>
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <ESP32Servo.h>
#include <BLEDevice.h>
#include <BLEScan.h>
#include <BLEAdvertisedDevice.h>
#include "secrets.h"

// ================= HARDWARE SETTINGS =================
const int servoPin = 13;
// Buzzer Pin Removed

const int SERVO_MIN_US = 500;
const int SERVO_MAX_US = 2500;

// ================= TUNING PARAMETERS =================
const unsigned long GATE_COOLDOWN_MS = 6000;
const int BLE_SCAN_DURATION = 5; // Seconds
const int RSSI_THRESHOLD = -85;

// ================= GLOBAL OBJECTS =================
Servo gateServo;
WiFiClientSecure espClient;
PubSubClient mqttClient(espClient);
BLEScan *pBLEScan;

// ================= STATE VARIABLES =================
volatile bool triggerBleScan = false;
volatile bool ownerFound = false;
volatile bool bleStopNow = false;
volatile bool gateIsMoving = false;

unsigned long lastGateOpenTime = 0;
unsigned long gateCloseTimer = 0;

TaskHandle_t bleTaskHandle;

// ================= BLE CALLBACK =================
const BLEUUID OWNER_CHAR_UUID("2222");

class MyAdvertisedDeviceCallbacks : public BLEAdvertisedDeviceCallbacks
{
  void onResult(BLEAdvertisedDevice device)
  {
    if (ownerFound)
      return;

    bool match =
        (device.haveServiceUUID() && device.isAdvertisingService(OWNER_CHAR_UUID)) ||
        (device.haveServiceData() && device.getServiceDataUUID().equals(OWNER_CHAR_UUID));

    if (match)
    {
      int rssi = device.getRSSI();

      if (rssi > RSSI_THRESHOLD)
      {
        Serial.printf("[BLE] Owner detected (RSSI %d)\n", rssi);
        ownerFound = true;
        bleStopNow = true;
      }
    }
  }
};

// ================= BLE TASK =================
void bleTask(void *parameter)
{
  Serial.println("[BLE TASK] Started");

  BLEDevice::init("");
  pBLEScan = BLEDevice::getScan();
  pBLEScan->setAdvertisedDeviceCallbacks(new MyAdvertisedDeviceCallbacks());
  pBLEScan->setActiveScan(true);
  pBLEScan->setInterval(100);
  pBLEScan->setWindow(80);

  for (;;)
  {
    if (triggerBleScan)
    {
      Serial.println("[BLE TASK] Starting scan...");
      ownerFound = false;
      bleStopNow = false;

      BLEScanResults results = pBLEScan->start(BLE_SCAN_DURATION, false);

      if (bleStopNow)
      {
        Serial.println("[BLE TASK] Early stop");
        pBLEScan->stop();
      }

      pBLEScan->clearResults();
      triggerBleScan = false;

      Serial.println("[BLE TASK] Scan completed");
    }

    vTaskDelay(100 / portTICK_PERIOD_MS);
  }
}

// ================= SERVO HELPERS =================
void setGate(int angle)
{
  gateServo.write(angle);
}

void notifyVisual()
{
  setGate(10);
  delay(150);
  setGate(0);
}

void triggerGateSequence(int angle, int durationMs)
{
  if (gateIsMoving)
    return;

  Serial.printf("[GATE] Moving to %d°\n", angle);
  gateIsMoving = true;
  setGate(angle);

  gateCloseTimer = millis() + durationMs;
  lastGateOpenTime = millis();
}

// ================= MQTT CALLBACK =================
void mqttCallback(char *topic, byte *payload, unsigned int length)
{
  String msg;
  for (unsigned int i = 0; i < length; i++)
    msg += (char)payload[i];
  Serial.printf("[MQTT] Message: %s\n", msg.c_str());

  if (msg == "scan_person")
  {
    if (millis() - lastGateOpenTime > GATE_COOLDOWN_MS)
    {
      Serial.println("[MAIN] Starting BLE scan");
      triggerBleScan = true;
    }
  }
  else if (msg == "open_small")
  {
    if (millis() - lastGateOpenTime > GATE_COOLDOWN_MS)
      triggerGateSequence(45, 900);
  }
  else if (msg == "open_big" || msg == "open_car")
  {
    if (millis() - lastGateOpenTime > GATE_COOLDOWN_MS)
      triggerGateSequence(90, 1200);
  }
}

// ================= MQTT CONNECT =================
void connectToMqtt()
{
  while (!mqttClient.connected())
  {
    Serial.print("[MQTT] Connecting... ");

    String clientId = "ESP32Gate-" + String(random(0xffff), HEX);

    if (mqttClient.connect(clientId.c_str(), MQTT_USER, MQTT_PASS))
    {
      Serial.println("OK");
      mqttClient.subscribe(MQTT_TOPIC);
      notifyVisual();
    }
    else
    {
      Serial.printf("Fail (rc=%d). Retrying...\n", mqttClient.state());
      delay(1500);
    }
  }
}

// ================= SETUP =================
void setup()
{
  Serial.begin(115200);
  delay(300);

  gateServo.attach(servoPin, SERVO_MIN_US, SERVO_MAX_US);
  gateServo.write(0);

  // Buzzer Setup REMOVED

  Serial.printf("[WiFi] Connecting to %s\n", WIFI_SSID);
  WiFi.begin(WIFI_SSID, WIFI_PASS);

  while (WiFi.status() != WL_CONNECTED)
  {
    Serial.print(".");
    delay(300);
  }
  Serial.println("\n[WiFi] Connected!");

  espClient.setInsecure();
  espClient.setHandshakeTimeout(20);

  mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
  mqttClient.setCallback(mqttCallback);

  xTaskCreatePinnedToCore(
      bleTask,
      "BLE_Task",
      4096,
      NULL,
      1,
      &bleTaskHandle,
      0);

  Serial.println("[SYSTEM] Ready");
}

// ================= MAIN LOOP =================
void loop()
{
  if (WiFi.status() != WL_CONNECTED)
  {
    Serial.println("[WiFi] Reconnecting...");
    WiFi.disconnect();
    WiFi.reconnect();
    delay(500);
    return;
  }

  if (!mqttClient.connected())
  {
    connectToMqtt();
  }

  mqttClient.loop();

  if (ownerFound)
  {
    Serial.println("[MAIN] Owner detected → Opening small gate");
    triggerGateSequence(45, 900);
    ownerFound = false;
  }

  if (gateIsMoving && millis() > gateCloseTimer)
  {
    Serial.println("[GATE] Auto-closing");
    setGate(0);
    gateIsMoving = false;
  }

  delay(20);
}