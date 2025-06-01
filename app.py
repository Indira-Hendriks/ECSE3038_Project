from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, time, timedelta
import requests
import re
import uuid
from typing import List

app = FastAPI()

# Enable CORS - add your development origins if needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://simple-smart-hub-client.netlify.app",
        "http://localhost:3000"  # For local development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage (replace with database in production)
current_settings = {
    "_id": str(uuid.uuid4()),
    "user_temp": 25.0,  # Default temperature
    "user_light": "18:00:00",  # Default light on time
    "light_time_off": "22:00:00"  # Default light off time
}
sensor_readings: List[dict] = []

# Data models
class SettingsRequest(BaseModel):
    user_temp: float
    user_light: str  # "HH:MM:SS" or "sunset"
    light_duration: str  # e.g. "1h", "30m"

class SettingsResponse(BaseModel):
    _id: str
    user_temp: float
    user_light: str
    light_time_off: str

class SensorData(BaseModel):
    temperature: float
    presence: bool
    datetime: str

def parse_duration(duration_str: str) -> timedelta:
    """Parse duration string like '4h' or '30m' into timedelta"""
    regex = re.compile(r'((?P<hours>\d+?)h)?((?P<minutes>\d+?)m)?((?P<seconds>\d+?)s)?')
    parts = regex.match(duration_str)
    if not parts:
        return None
    parts = parts.groupdict()
    time_params = {}
    for name, param in parts.items():
        if param:
            time_params[name] = int(param)
    return timedelta(**time_params)

def get_sunset_time() -> time:
    """Get sunset time for Jamaica (Kingston coordinates)"""
    try:
        response = requests.get(
            "https://api.sunrise-sunset.org/json?lat=17.9970&lng=-76.7936&formatted=0",
            timeout=5
        )
        response.raise_for_status()
        data = response.json()
        sunset_str = data['results']['sunset']
        return datetime.fromisoformat(sunset_str.replace("Z", "+00:00")).time()
    except Exception as e:
        print(f"Error getting sunset time: {e}")
        return time(18, 0)  # Fallback to 6:00 PM

@app.get("/")
def read_root():
    return {"message": "Smart Hub API is running"}

@app.put("/settings", response_model=SettingsResponse)
async def update_settings(settings: SettingsRequest):
    # Calculate turn-on time
    if settings.user_light.lower() == "sunset":
        turn_on_time = get_sunset_time()
        user_light_response = turn_on_time.isoformat()
    else:
        try:
            turn_on_time = time.fromisoformat(settings.user_light)
            user_light_response = settings.user_light
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid time format. Use HH:MM:SS or 'sunset'"
            )

    # Calculate turn-off time
    duration = parse_duration(settings.light_duration)
    if not duration:
        raise HTTPException(
            status_code=400,
            detail="Invalid duration format. Use like '1h', '30m', etc."
        )
    
    turn_off_time = (
        datetime.combine(datetime.today(), turn_on_time) + duration
    ).time()

    response_data = {
        "_id": str(uuid.uuid4()),
        "user_temp": settings.user_temp,
        "user_light": user_light_response,
        "light_time_off": turn_off_time.isoformat()
    }
    
    current_settings.update(response_data)
    return response_data

@app.post("/sensor-data")
async def receive_sensor_data(data: SensorData):
    """Store sensor data from ESP32"""
    try:
        # Validate datetime or use current time if invalid
        datetime.fromisoformat(data.datetime)
    except ValueError:
        data.datetime = datetime.now().isoformat()
    
    # Store the data
    sensor_readings.append(data.dict())
    
    # Keep only the last 100 readings
    if len(sensor_readings) > 100:
        sensor_readings.pop(0)
    
    return {"message": "Data received"}

@app.get("/graph")
async def get_graph_data(size: int = Query(10, gt=0, le=100)):
    """Get recent sensor data for graphing"""
    return sensor_readings[-size:]

@app.get("/control")
async def get_control_commands():
    """Get control commands for ESP32 based on current conditions"""
    if not current_settings["_id"] or not sensor_readings:
        return {"fan": False, "light": False}
    
    latest = sensor_readings[-1]
    now = datetime.now().time()
    
    try:
        light_on_time = time.fromisoformat(current_settings["user_light"])
        light_off_time = time.fromisoformat(current_settings["light_time_off"])
    except ValueError:
        return {"fan": False, "light": False}
    
    # Combined logic: presence + temperature/time conditions
    return {
        "fan": (
            latest["temperature"] > current_settings["user_temp"] and 
            latest["presence"]
        ),
        "light": (
            light_on_time <= now <= light_off_time and 
            latest["presence"]
        )
    }

@app.get("/settings")
async def get_current_settings():
    """Get current settings"""
    return current_settings