#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// Configuration - update these values
const char* ssid = "MonaConnect";
const char* password = "";
const char* apiBaseUrl = "https://ecse3038-project-wcrk.onrender.com"; 

// Pin definitions
const int tempSensorPin = 4;    // Analog pin for temperature sensor
const int pirSensorPin = 15;     // Digital pin for PIR sensor
const int fanControlPin = 23;    // GPIO for fan control (MOSFET gate)
const int lightControlPin = 22;  // GPIO for light control (MOSFET gate)

// Variables
unsigned long lastSensorUpdate = 0;
const long sensorUpdateInterval = 5000;  // 5 seconds
bool currentFanState = false;
bool currentLightState = false;

void connectToWiFi() {
  Serial.println("Connecting to WiFi...");
  WiFi.begin(ssid, password);
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
}

float readTemperature() {
  // Read analog value and convert to temperature
  int analogValue = analogRead(tempSensorPin);
  float voltage = analogValue * (3.3 / 4095.0);
  float temperature = (voltage - 0.5) * 100;  // LM35 approximation
  
  return temperature;
}

bool detectPresence() {
  return digitalRead(pirSensorPin) == HIGH;
}

void sendSensorData(float temperature, bool presence) {
  if (WiFi.status() != WL_CONNECTED) {
    connectToWiFi();
    return;
  }

  HTTPClient http;
  String url = String(apiBaseUrl) + "/sensor-data";
  
  http.begin(url);
  http.addHeader("Content-Type", "application/json");

  // Create JSON payload
  DynamicJsonDocument doc(256);
  doc["temperature"] = temperature;
  doc["presence"] = presence;
  doc["datetime"] = "2023-01-01T00:00:00";  // Replace with actual time if you have RTC
  
  String payload;
  serializeJson(doc, payload);

  int httpResponseCode = http.POST(payload);
  
  if (httpResponseCode > 0) {
    Serial.print("HTTP Response code: ");
    Serial.println(httpResponseCode);
  } else {
    Serial.print("Error code: ");
    Serial.println(httpResponseCode);
  }
  
  http.end();
}

void getControlCommands() {
  if (WiFi.status() != WL_CONNECTED) {
    connectToWiFi();
    return;
  }

  HTTPClient http;
  String url = String(apiBaseUrl) + "/control";
  
  http.begin(url);
  int httpResponseCode = http.GET();
  
  if (httpResponseCode == HTTP_CODE_OK) {
    String payload = http.getString();
    
    DynamicJsonDocument doc(256);
    deserializeJson(doc, payload);

    bool fanCommand = doc["fan"];
    bool lightCommand = doc["light"];
    
    // Only update if state changed
    if (fanCommand != currentFanState) {
      digitalWrite(fanControlPin, fanCommand ? HIGH : LOW);
      currentFanState = fanCommand;
      Serial.println(fanCommand ? "Fan turned ON" : "Fan turned OFF");
    }
    
    if (lightCommand != currentLightState) {
      digitalWrite(lightControlPin, lightCommand ? HIGH : LOW);
      currentLightState = lightCommand;
      Serial.println(lightCommand ? "Light turned ON" : "Light turned OFF");
    }
  } else {
    Serial.print("Error getting control commands: ");
    Serial.println(httpResponseCode);
  }
  
  http.end();
}

void setup() {
  Serial.begin(115200);
  
  // Initialize pins
  pinMode(tempSensorPin, INPUT);
  pinMode(pirSensorPin, INPUT);
  pinMode(fanControlPin, OUTPUT);
  pinMode(lightControlPin, OUTPUT);
  
  // Start with devices off
  digitalWrite(fanControlPin, LOW);
  digitalWrite(lightControlPin, LOW);
  
  // Connect to WiFi
  connectToWiFi();
}

void loop() {
  unsigned long currentMillis = millis();
  
  // Regular sensor updates
  if (currentMillis - lastSensorUpdate >= sensorUpdateInterval) {
    float temperature = readTemperature();
    bool presence = detectPresence();
    
    Serial.print("Temperature: ");
    Serial.print(temperature);
    Serial.print("°C, Presence: ");
    Serial.println(presence ? "Detected" : "Not detected");
    
    sendSensorData(temperature, presence);
    getControlCommands();
    
    lastSensorUpdate = currentMillis;
  }
  
  // Handle WiFi disconnections
  if (WiFi.status() != WL_CONNECTED) {
    connectToWiFi();
  }
  
  delay(100);  // Small delay to prevent watchdog timer issues
}