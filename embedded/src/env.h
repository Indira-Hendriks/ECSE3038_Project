// WiFi Configuration for Wokwi simulation
const char* SSID = "Wokwi-GUEST";
const char* PASS = "";
const int CHANNEL = 6; 

// API Configuration
const char* ENDPOINT = "https://ecse3038-project-wcrk.onrender.com";


// Pin Definitions 
const int TEMP_SENSOR_PIN = 4;   // DS18B20 data connected to GPIO4
const int PIR_PIN = 15;          // PIR sensor output connected to GPIO15
const int LIGHT_RELAY_PIN = 22;  // Light control relay connected to GPIO22
const int FAN_RELAY_PIN = 23;    // Fan control relay connected to GPIO23

// Device Constants
const int UPDATE_INTERVAL = 5000;  // 5 seconds between sensor readings