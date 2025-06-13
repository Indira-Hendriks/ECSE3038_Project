// #include <Arduino.h>
// #include <WiFi.h>
// #include <HTTPClient.h>
// #include <ArduinoJson.h>

// // Configuration - update these values
// const char* ssid = "MonaConnect";
// const char* password = "";
// const char* apiBaseUrl = "https://ecse3038-project-wcrk.onrender.com"; 

// // Pin definitions
// const int tempSensorPin = 4;    // Analog pin for temperature sensor
// const int pirSensorPin = 15;     // Digital pin for PIR sensor
// const int fanControlPin = 23;    // GPIO for fan control (MOSFET gate)
// const int lightControlPin = 22;  // GPIO for light control (MOSFET gate)

// // Variables
// unsigned long lastSensorUpdate = 0;
// const long sensorUpdateInterval = 5000;  // 5 seconds
// bool currentFanState = false;
// bool currentLightState = false;

// void connectToWiFi() {
//   Serial.println("Connecting to WiFi...");
//   WiFi.begin(ssid, password);
  
//   while (WiFi.status() != WL_CONNECTED) {
//     delay(500);
//     Serial.print(".");
//   }
  
//   Serial.println("");
//   Serial.println("WiFi connected");
//   Serial.println("IP address: ");
//   Serial.println(WiFi.localIP());
// }

// float readTemperature() {
//   // Read analog value and convert to temperature
//   int analogValue = analogRead(tempSensorPin);
//   float voltage = analogValue * (3.3 / 4095.0);
//   float temperature = (voltage - 0.5) * 100;  // LM35 approximation
  
//   return temperature;
// }

// bool detectPresence() {
//   return digitalRead(pirSensorPin) == HIGH;
// }

// void sendSensorData(float temperature, bool presence) {
//   if (WiFi.status() != WL_CONNECTED) {
//     connectToWiFi();
//     return;
//   }

//   HTTPClient http;
//   String url = String(apiBaseUrl) + "/sensor-data";
  
//   http.begin(url);
//   http.addHeader("Content-Type", "application/json");

//   // Create JSON payload
//   DynamicJsonDocument doc(256);
//   doc["temperature"] = temperature;
//   doc["presence"] = presence;
//   doc["datetime"] = "2023-01-01T00:00:00";  // Replace with actual time if you have RTC
  
//   String payload;
//   serializeJson(doc, payload);

//   int httpResponseCode = http.POST(payload);
  
//   if (httpResponseCode > 0) {
//     Serial.print("HTTP Response code: ");
//     Serial.println(httpResponseCode);
//   } else {
//     Serial.print("Error code: ");
//     Serial.println(httpResponseCode);
//   }
  
//   http.end();
// }

// void getControlCommands() {
//   if (WiFi.status() != WL_CONNECTED) {
//     connectToWiFi();
//     return;
//   }

//   HTTPClient http;
//   String url = String(apiBaseUrl) + "/control";
  
//   http.begin(url);
//   int httpResponseCode = http.GET();
  
//   if (httpResponseCode == HTTP_CODE_OK) {
//     String payload = http.getString();
    
//     DynamicJsonDocument doc(256);
//     deserializeJson(doc, payload);

//     bool fanCommand = doc["fan"];
//     bool lightCommand = doc["light"];
    
//     // Only update if state changed
//     if (fanCommand != currentFanState) {
//       digitalWrite(fanControlPin, fanCommand ? HIGH : LOW);
//       currentFanState = fanCommand;
//       Serial.println(fanCommand ? "Fan turned ON" : "Fan turned OFF");
//     }
    
//     if (lightCommand != currentLightState) {
//       digitalWrite(lightControlPin, lightCommand ? HIGH : LOW);
//       currentLightState = lightCommand;
//       Serial.println(lightCommand ? "Light turned ON" : "Light turned OFF");
//     }
//   } else {
//     Serial.print("Error getting control commands: ");
//     Serial.println(httpResponseCode);
//   }
  
//   http.end();
// }

// void setup() {
//   Serial.begin(115200);
  
//   // Initialize pins
//   pinMode(tempSensorPin, INPUT);
//   pinMode(pirSensorPin, INPUT);
//   pinMode(fanControlPin, OUTPUT);
//   pinMode(lightControlPin, OUTPUT);
  
//   // Start with devices off
//   digitalWrite(fanControlPin, LOW);
//   digitalWrite(lightControlPin, LOW);
  
//   // Connect to WiFi
//   connectToWiFi();
// }

// void loop() {
//   unsigned long currentMillis = millis();
  
//   // Regular sensor updates
//   if (currentMillis - lastSensorUpdate >= sensorUpdateInterval) {
//     float temperature = readTemperature();
//     bool presence = detectPresence();
    
//     Serial.print("Temperature: ");
//     Serial.print(temperature);
//     Serial.print("°C, Presence: ");
//     Serial.println(presence ? "Detected" : "Not detected");
    
//     sendSensorData(temperature, presence);
//     getControlCommands();
    
//     lastSensorUpdate = currentMillis;
//   }
  
//   // Handle WiFi disconnections
//   if (WiFi.status() != WL_CONNECTED) {
//     connectToWiFi();
//   }
  
//   delay(100);  // Small delay to prevent watchdog timer issues
// }


// CODE FOR WOKWI DEMONSTARTION:
#include <Arduino.h>
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include "env.h"

// Initialize OneWire bus
OneWire oneWire(TEMP_SENSOR_PIN);
DallasTemperature sensors(&oneWire);
WiFiClientSecure client;

unsigned long lastAttemptTime = 0;
const unsigned long retryInterval = 10000; // Retry WiFi every 10 sec

void setup() {
    Serial.begin(115200);
    
    pinMode(LIGHT_RELAY_PIN, OUTPUT);
    pinMode(FAN_RELAY_PIN, OUTPUT);
    pinMode(PIR_PIN, INPUT);
    
    digitalWrite(LIGHT_RELAY_PIN, LOW);
    digitalWrite(FAN_RELAY_PIN, LOW);
    
    sensors.begin();
    connectToWiFi();
}

void connectToWiFi() {
    Serial.println("Connecting to WiFi...");
    WiFi.begin(SSID, PASS, CHANNEL);
    
    unsigned long startTime = millis();
    while (WiFi.status() != WL_CONNECTED && millis() - startTime < 10000) {
        delay(500);
        Serial.print(".");
    }
    
    if (WiFi.status() == WL_CONNECTED) {
        Serial.println("\nConnected to WiFi!");
        Serial.print("IP Address: ");
        Serial.println(WiFi.localIP());
        client.setInsecure();  // Skip certificate validation
    } else {
        Serial.println("\nFailed to connect to WiFi");
    }
}

void loop() {
    unsigned long currentTime = millis();
    
    if (WiFi.status() != WL_CONNECTED) {
        if (currentTime - lastAttemptTime >= retryInterval) {
            Serial.println("Reconnecting to WiFi...");
            WiFi.reconnect();
            lastAttemptTime = currentTime;
        }
        delay(1000);
        return;
    }

    sensors.requestTemperatures();
    float temperature = sensors.getTempCByIndex(0);
    bool presence = digitalRead(PIR_PIN) == HIGH;

    // Validate sensor output
    if (isnan(temperature)) {
        Serial.println("Temperature read failed.");
        delay(UPDATE_INTERVAL);
        return;
    }

    Serial.printf("Sensor Readings - Temp: %.2f°C, Presence: %s\n",
                  temperature, presence ? "Yes" : "No");

    if (!sendSensorData(temperature, presence)) {
        Serial.println("Failed to send sensor data");
    }

    if (!getControlCommands()) {
        Serial.println("Failed to get control commands");
    }

    delay(UPDATE_INTERVAL);
}

bool sendSensorData(float temp, bool presence) {
    HTTPClient http;
    bool success = false;
    
    if (http.begin(client, String(ENDPOINT) + "/sensor-data")) {
        http.addHeader("Content-Type", "application/json");
        
        DynamicJsonDocument doc(128);
        doc["temperature"] = temp;
        doc["presence"] = presence;

        String payload;
        serializeJson(doc, payload);
        Serial.print("Sending JSON: ");
        Serial.println(payload);

        int httpCode = http.POST(payload);
        if (httpCode == HTTP_CODE_OK) {
            Serial.println("Sensor data sent successfully");
            success = true;
        } else {
            Serial.printf("HTTP POST failed with code: %d\n", httpCode);
            Serial.println(http.getString());
        }
        http.end();
    } else {
        Serial.println("Unable to start HTTP connection for sensor data.");
    }
    
    return success;
}

bool getControlCommands() {
    HTTPClient http;
    bool success = false;

    if (http.begin(client, String(ENDPOINT) + "/control")) {
        int httpCode = http.GET();
        if (httpCode == HTTP_CODE_OK) {
            String payload = http.getString();
            DynamicJsonDocument doc(128);
            DeserializationError error = deserializeJson(doc, payload);
            
            if (!error) {
                bool fanState = doc["fan"];
                bool lightState = doc["light"];
                
                digitalWrite(FAN_RELAY_PIN, fanState ? HIGH : LOW);
                digitalWrite(LIGHT_RELAY_PIN, lightState ? HIGH : LOW);
                
                Serial.printf("Control - Fan: %s, Light: %s\n",
                              fanState ? "ON" : "OFF",
                              lightState ? "ON" : "OFF");
                success = true;
            } else {
                Serial.print("JSON parse failed: ");
                Serial.println(error.c_str());
            }
        } else {
            Serial.printf("HTTP GET failed with code: %d\n", httpCode);
        }
        http.end();
    } else {
        Serial.println("Unable to start HTTP connection for control.");
    }

    return success;
}
