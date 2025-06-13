# from fastapi import FastAPI, HTTPException, Query
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# from datetime import datetime, time, timedelta
# import requests
# import re
# import uuid
# from typing import List, Optional

# app = FastAPI()

# # Enable CORS
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=[
#         "https://simple-smart-hub-client.netlify.app",
#         "http://localhost:3000"  # For local development
#     ],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # In-memory storage (replace with database in production)
# current_settings = {
#     "_id": str(uuid.uuid4()),
#     "user_temp": 25.0,  # Default temperature threshold
#     "user_light": "18:00:00",  # Default light on time
#     "light_time_off": "22:00:00"  # Default light off time
# }

# # Store sensor readings with API-generated timestamps
# sensor_readings: List[dict] = []

# # Data models
# class SettingsRequest(BaseModel):
#     user_temp: float
#     user_light: str  # Either "HH:MM:SS" or "sunset"
#     light_duration: str  # Format like "4h", "30m", "1h30m"

# class SettingsResponse(BaseModel):
#     _id: str
#     user_temp: float
#     user_light: str
#     light_time_off: str

# class SensorData(BaseModel):
#     temperature: float
#     presence: bool

# # Helper functions
# def parse_duration(duration_str: str) -> Optional[timedelta]:
#     """Parse duration string like '4h' or '30m' into timedelta"""
#     regex = re.compile(r'((?P<hours>\d+?)h)?((?P<minutes>\d+?)m)?((?P<seconds>\d+?)s)?')
#     parts = regex.match(duration_str)
#     if not parts:
#         return None
#     parts = parts.groupdict()
#     time_params = {}
#     for name, param in parts.items():
#         if param:
#             time_params[name] = int(param)
#     return timedelta(**time_params)

# def get_sunset_time() -> time:
#     """Get sunset time for Jamaica (Kingston coordinates)"""
#     try:
#         response = requests.get(
#             "https://api.sunrise-sunset.org/json?lat=17.9970&lng=-76.7936&formatted=0",
#             timeout=5
#         )
#         response.raise_for_status()
#         data = response.json()
#         sunset_str = data['results']['sunset']
#         return datetime.fromisoformat(sunset_str.replace("Z", "+00:00")).time()
#     except Exception as e:
#         print(f"Error getting sunset time: {e}")
#         return time(18, 0)  # Fallback to 6:00 PM

# # API endpoints
# @app.get("/")
# def read_root():
#     return {"message": "Smart Hub API is running"}

# @app.put("/settings", response_model=SettingsResponse)
# async def update_settings(settings: SettingsRequest):
#     # Calculate turn-on time
#     if settings.user_light.lower() == "sunset":
#         turn_on_time = get_sunset_time()
#         user_light_response = turn_on_time.isoformat()
#     else:
#         try:
#             turn_on_time = time.fromisoformat(settings.user_light)
#             user_light_response = settings.user_light
#         except ValueError:
#             raise HTTPException(
#                 status_code=400,
#                 detail="Invalid time format. Use HH:MM:SS or 'sunset'"
#             )

#     # Calculate turn-off time
#     duration = parse_duration(settings.light_duration)
#     if not duration:
#         raise HTTPException(
#             status_code=400,
#             detail="Invalid duration format. Use like '1h', '30m', etc."
#         )
    
#     turn_off_time = (
#         datetime.combine(datetime.today(), turn_on_time) + duration
#     ).time()

#     # Update settings
#     response_data = {
#         "_id": str(uuid.uuid4()),
#         "user_temp": settings.user_temp,
#         "user_light": user_light_response,
#         "light_time_off": turn_off_time.isoformat()
#     }
    
#     current_settings.update(response_data)
#     return response_data

# @app.post("/sensor-data")
# async def receive_sensor_data(data: SensorData):
#     """Store sensor data with API-generated timestamp"""
#     reading = {
#         "temperature": data.temperature,
#         "presence": data.presence,
#         "datetime": datetime.now().isoformat()  # API adds the timestamp
#     }
    
#     sensor_readings.append(reading)
    
#     # Keep only the last 100 readings
#     if len(sensor_readings) > 100:
#         sensor_readings.pop(0)
    
#     return {"message": "Data received"}

# @app.get("/graph")
# async def get_graph_data(size: int = Query(10, gt=0, le=100)):
#     """Get recent sensor data for graphing"""
#     return sensor_readings[-size:]

# @app.get("/control")
# async def get_control_commands():
#     """Determine control commands based on settings and sensor data"""
#     if not sensor_readings:
#         return {"fan": False, "light": False}
    
#     latest = sensor_readings[-1]
#     now = datetime.now().time()
    
#     try:
#         light_on_time = time.fromisoformat(current_settings["user_light"])
#         light_off_time = time.fromisoformat(current_settings["light_time_off"])
#     except ValueError:
#         return {"fan": False, "light": False}
    
#     # Combined logic: presence + temperature/time conditions
#     return {
#         "fan": (
#             latest["temperature"] > current_settings["user_temp"] and 
#             latest["presence"]
#         ),
#         "light": (
#             light_on_time <= now <= light_off_time and 
#             latest["presence"]
#         )
#     }

# @app.get("/settings")
# async def get_current_settings():
#     """Get current settings"""
#     return current_settings

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, time, timedelta
import requests
import re
import uuid
import logging
from typing import List, Optional
import pytz

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://simple-smart-hub-client.netlify.app",
        "http://localhost:3000",
        "https://wokwi.com"  # For Wokwi simulation
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage with persistence simulation
current_settings = {
    "_id": str(uuid.uuid4()),
    "user_temp": 25.0,
    "user_light": "18:00:00",
    "light_time_off": "22:00:00",
    "last_updated": datetime.now().isoformat()
}

# Store sensor readings with API-generated timestamps
sensor_readings: List[dict] = []

# Data models
class SettingsRequest(BaseModel):
    user_temp: float
    user_light: str  # Either "HH:MM:SS" or "sunset"
    light_duration: str  # Format like "4h", "30m", "1h30m"

class SettingsResponse(BaseModel):
    _id: str
    user_temp: float
    user_light: str
    light_time_off: str
    last_updated: str

class SensorData(BaseModel):
    temperature: float
    presence: bool

# Helper functions
def parse_duration(duration_str: str) -> Optional[timedelta]:
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
    """Get sunset time for Jamaica (Kingston coordinates) with fallback"""
    try:
        response = requests.get(
            "https://api.sunrise-sunset.org/json?lat=17.9970&lng=-76.7936&formatted=0",
            timeout=3
        )
        response.raise_for_status()
        data = response.json()
        sunset_str = data['results']['sunset']
        sunset_time = datetime.fromisoformat(sunset_str.replace("Z", "+00:00")).time()
        logger.info(f"Retrieved sunset time: {sunset_time}")
        return sunset_time
    except Exception as e:
        logger.error(f"Error getting sunset time: {e}, using fallback 18:00")
        return time(18, 0)  # Fallback to 6:00 PM

def log_current_state():
    """Log current system state for debugging"""
    logger.info(f"Current Settings: {current_settings}")
    if sensor_readings:
        logger.info(f"Latest Sensor Reading: {sensor_readings[-1]}")
    else:
        logger.info("No sensor readings available")

# API endpoints
@app.get("/")
def read_root():
    return {"message": "Smart Hub API is running", "status": "healthy"}

@app.put("/settings", response_model=SettingsResponse)
async def update_settings(settings: SettingsRequest):
    logger.info(f"Received settings update: {settings.dict()}")
    
    # Calculate turn-on time
    if settings.user_light.lower() == "sunset":
        turn_on_time = get_sunset_time()
        user_light_response = turn_on_time.isoformat()
    else:
        try:
            turn_on_time = time.fromisoformat(settings.user_light)
            user_light_response = settings.user_light
        except ValueError:
            logger.error(f"Invalid time format received: {settings.user_light}")
            raise HTTPException(
                status_code=400,
                detail="Invalid time format. Use HH:MM:SS or 'sunset'"
            )

    # Calculate turn-off time
    duration = parse_duration(settings.light_duration)
    if not duration:
        logger.error(f"Invalid duration format received: {settings.light_duration}")
        raise HTTPException(
            status_code=400,
            detail="Invalid duration format. Use like '1h', '30m', etc."
        )
    
    turn_off_time = (
        datetime.combine(datetime.today(), turn_on_time) + duration
    ).time()

    # Update settings
    response_data = {
        "_id": str(uuid.uuid4()),
        "user_temp": settings.user_temp,
        "user_light": user_light_response,
        "light_time_off": turn_off_time.isoformat(),
        "last_updated": datetime.now().isoformat()
    }
    
    current_settings.update(response_data)
    logger.info(f"Updated settings: {current_settings}")
    
    log_current_state()
    return response_data

@app.post("/sensor-data")
async def receive_sensor_data(data: SensorData):
    """Store sensor data with API-generated timestamp"""
    # Validate sensor data
    if data.temperature < -20 or data.temperature > 60:
        logger.warning(f"Invalid temperature reading: {data.temperature}")
        raise HTTPException(status_code=400, detail="Invalid temperature reading")
    
    reading = {
        "temperature": data.temperature,
        "presence": data.presence,
        "datetime": datetime.now(pytz.utc).isoformat()  # Timezone-aware timestamp
    }
    
    sensor_readings.append(reading)
    logger.info(f"Stored sensor reading: {reading}")
    
    # Keep only the last 100 readings
    if len(sensor_readings) > 100:
        sensor_readings.pop(0)
    
    return {"message": "Data received", "status": "success"}

@app.get("/graph")
async def get_graph_data(size: int = Query(10, gt=0, le=100)):
    """Get recent sensor data for graphing"""
    logger.info(f"Requested graph data, returning last {size} readings")
    return sensor_readings[-size:]

@app.get("/control")
async def get_control_commands():
    """Determine control commands based on settings and sensor data"""
    logger.info("Calculating control commands...")
    log_current_state()
    
    if not sensor_readings:
        logger.warning("No sensor readings available, defaulting to OFF")
        return {"fan": False, "light": False}
    
    latest = sensor_readings[-1]
    now = datetime.now(pytz.utc).time()  # Use UTC time
    
    try:
        light_on_time = time.fromisoformat(current_settings["user_light"])
        light_off_time = time.fromisoformat(current_settings["light_time_off"])
    except ValueError as e:
        logger.error(f"Time parsing error: {e}")
        return {"fan": False, "light": False}
    
    # Combined logic: presence + temperature/time conditions
    fan_state = (
        latest["temperature"] > current_settings["user_temp"] and 
        latest["presence"]
    )
    light_state = (
        light_on_time <= now <= light_off_time and 
        latest["presence"]
    )
    
    logger.info(
        f"Control decision - Fan: {fan_state} (Temp: {latest['temperature']} > {current_settings['user_temp']} "
        f"& Presence: {latest['presence']}), Light: {light_state} "
        f"(Time: {now} between {light_on_time}-{light_off_time} & Presence: {latest['presence']})"
    )
    
    return {
        "fan": fan_state,
        "light": light_state,
        "timestamp": datetime.now(pytz.utc).isoformat()
    }

@app.get("/settings")
async def get_current_settings():
    """Get current settings"""
    logger.info("Returning current settings")
    return current_settings

@app.get("/debug")
async def debug_info():
    """Debug endpoint to see full system state"""
    return {
        "settings": current_settings,
        "latest_sensor": sensor_readings[-1] if sensor_readings else None,
        "sensor_count": len(sensor_readings),
        "server_time": datetime.now(pytz.utc).isoformat(),
        "system_status": "operational"
    }