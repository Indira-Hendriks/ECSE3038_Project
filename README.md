# ESP32 Smart Hub with Temperature, Presence Detection, and Automated Light/Fan Control

## Project Overview

This project demonstrates how to connect an ESP32 to a Wi-Fi network, send temperature and presence data to a FastAPI backend via HTTPS, and control a fan and light based on smart logic. The backend allows users to set thresholds such as temperature and light schedules (including automatic sunset-based lighting), and it responds with control commands the ESP32 can act on.

## Features

- **Wi-Fi Connectivity**: Connects to a local network and communicates securely with the API.
- **Secure API Requests**: Uses `WiFiClientSecure` and `HTTPClient` to send and receive JSON data via HTTPS.
- **Temperature and Motion Monitoring**: Reads temperature from a DS18B20 sensor and detects motion using a PIR sensor.
- **Fan and Light Automation**: Controls fan and light relays based on temperature, motion, and time logic from the backend.
- **Customizable Logic via API**: Light timing can be user-defined or automatically set to sunset in Jamaica.
- **Recent Data Graphing**: API stores and provides recent sensor data for visualization.
- **Fallback and Error Handling**: Handles API failures, incorrect input formats, and sunset API timeouts gracefully.

## Code Breakdown

### `setup()`

Initializes hardware components and Wi-Fi connection.

- Starts Serial Communication at 115200 baud.
- Sets pin modes for PIR sensor and relays.
- Initializes OneWire and DS18B20 temperature sensor.
- Connects to Wi-Fi using `WiFi.begin(SSID, PASS, CHANNEL);`.
- Displays connection status over Serial.
- Configures HTTPS client with `client.setInsecure()` for testing.

### `loop()`

Handles continuous device logic and API interaction.

#### Wi-Fi Reconnection

- If Wi-Fi is disconnected, attempts reconnection every cycle.

#### Send Sensor Data to API (`POST /sensor-data`)

- Reads temperature from DS18B20 and motion from PIR.
- Sends JSON data to FastAPI server via HTTPS.
- Prints server response in Serial Monitor.
- Handles HTTP errors.

#### Get Control Commands from API (`GET /control`)

- Sends GET request to retrieve fan and light commands.
- Parses JSON response to extract control signals.
- Updates GPIO output pins to turn fan/light ON or OFF.
- Handles HTTP and JSON errors.

#### Delay

- Waits for a fixed interval (e.g., 60 seconds) before repeating the loop.

## Expected Serial Monitor Output
<img width="386" alt="image" src="https://github.com/user-attachments/assets/00086373-08e7-4c0f-9945-aead2befebe0" />


## Additional Notes
Simulated on Wokwi: No physical ESP32 hardware is required. All sensors and outputs can be emulated virtually.

Sunset Time API: The backend fetches sunset time from sunrise-sunset.org for Kingston, Jamaica. If the request fails, it defaults to 6:00 PM.

Error Handling: The API validates time formats (HH:MM:SS) and durations (1h, 30m, etc.). ESP32 handles Wi-Fi and HTTPS errors with retries.

Security Note: For simulation, client.setInsecure() bypasses SSL verification. In production, install CA certs or use fingerprint verification.

In-Memory Storage: The backend uses in-memory storage for settings and sensor data. 



## How to Use

### 1. Update `env.h` with your Wi-Fi credentials and endpoint:

```cpp
#define SSID "your_wifi_ssid"
#define PASS "your_wifi_password"
#define CHANNEL 1
#define ENDPOINT "https://your-api-endpoint.com"

