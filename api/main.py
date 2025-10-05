from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import httpx
import os
import json
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="WeatherSphere API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Local frontend URL
        "https://nasa-hack-88nz.onrender.com",  # Backend itself (self-referencing)
        "https://nasa-hack-pi.vercel.app",  # Vercel frontend URL
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
OPENWEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5"

# Supabase Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Simple Supabase HTTP client
class SupabaseClient:
    def __init__(self, url: str, key: str):
        self.url = url
        self.key = key
        self.headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }

    async def insert(self, table: str, data: dict):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.url}/rest/v1/{table}",
                headers=self.headers,
                json=data
            )
            return response

    async def select(self, table: str):
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.url}/rest/v1/{table}",
                headers=self.headers
            )
            return response

# Initialize Supabase client
supabase = None
if SUPABASE_URL and SUPABASE_KEY and not SUPABASE_URL.startswith("your_"):
    try:
        supabase = SupabaseClient(SUPABASE_URL, SUPABASE_KEY)
        print("Supabase client initialized successfully")
    except Exception as e:
        print(f"Warning: Failed to initialize Supabase client: {e}")
        supabase = None

class WeatherResponse(BaseModel):
    current: Dict[str, Any]
    forecast: List[Dict[str, Any]]

class LocationRegistration(BaseModel):
    chat_id: int
    city: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class AlertResponse(BaseModel):
    message: str
    users_processed: int
    alerts_sent: int

@app.get("/")
async def hello_world():
    return {"message": "Hello World from WeatherSphere API"}

@app.get("/weather", response_model=WeatherResponse)
async def get_weather(city: str):
    if not OPENWEATHER_API_KEY:
        raise HTTPException(status_code=500, detail="OpenWeather API key not configured")

    if not city:
        raise HTTPException(status_code=400, detail="City parameter is required")

    async with httpx.AsyncClient() as client:
        try:
            # Fetch current weather
            current_url = f"{OPENWEATHER_BASE_URL}/weather"
            current_params = {
                "q": city,
                "appid": OPENWEATHER_API_KEY,
                "units": "metric"
            }

            current_response = await client.get(current_url, params=current_params)
            if current_response.status_code != 200:
                if current_response.status_code == 404:
                    raise HTTPException(status_code=404, detail=f"City '{city}' not found")
                else:
                    raise HTTPException(status_code=500, detail="Failed to fetch current weather data")

            current_data = current_response.json()

            # Fetch 5-day forecast
            forecast_url = f"{OPENWEATHER_BASE_URL}/forecast"
            forecast_params = {
                "q": city,
                "appid": OPENWEATHER_API_KEY,
                "units": "metric"
            }

            forecast_response = await client.get(forecast_url, params=forecast_params)
            if forecast_response.status_code != 200:
                raise HTTPException(status_code=500, detail="Failed to fetch forecast data")

            forecast_data = forecast_response.json()

            # Process and clean the data
            processed_current = {
                "city": current_data["name"],
                "country": current_data["sys"]["country"],
                "temperature": current_data["main"]["temp"],
                "feels_like": current_data["main"]["feels_like"],
                "humidity": current_data["main"]["humidity"],
                "pressure": current_data["main"]["pressure"],
                "description": current_data["weather"][0]["description"],
                "icon": current_data["weather"][0]["icon"],
                "wind_speed": current_data["wind"]["speed"],
                "wind_direction": current_data["wind"].get("deg", 0),
                "visibility": current_data.get("visibility", 0) / 1000,  # Convert to km
                "timestamp": current_data["dt"]
            }

            # Process forecast (group by day)
            forecast_list = []
            daily_forecasts = {}

            for item in forecast_data["list"]:
                date = item["dt_txt"].split(" ")[0]
                if date not in daily_forecasts:
                    daily_forecasts[date] = {
                        "date": date,
                        "temp_min": item["main"]["temp_min"],
                        "temp_max": item["main"]["temp_max"],
                        "description": item["weather"][0]["description"],
                        "icon": item["weather"][0]["icon"],
                        "humidity": item["main"]["humidity"],
                        "wind_speed": item["wind"]["speed"],
                        "times": []
                    }
                else:
                    # Update min/max temps
                    daily_forecasts[date]["temp_min"] = min(daily_forecasts[date]["temp_min"], item["main"]["temp_min"])
                    daily_forecasts[date]["temp_max"] = max(daily_forecasts[date]["temp_max"], item["main"]["temp_max"])

                # Add time-specific data
                daily_forecasts[date]["times"].append({
                    "time": item["dt_txt"].split(" ")[1],
                    "temperature": item["main"]["temp"],
                    "description": item["weather"][0]["description"],
                    "icon": item["weather"][0]["icon"]
                })

            # Convert to list and limit to 5 days
            forecast_list = list(daily_forecasts.values())[:5]

            return WeatherResponse(
                current=processed_current,
                forecast=forecast_list
            )

        except httpx.RequestError:
            raise HTTPException(status_code=500, detail="Failed to connect to weather service")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

@app.post("/register_location", response_model=dict)
async def register_location(location: LocationRegistration):
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")

    # Validate input
    if not location.chat_id:
        raise HTTPException(status_code=400, detail="Chat ID is required")

    if not location.city and not (location.latitude and location.longitude):
        raise HTTPException(status_code=400, detail="Either city name or coordinates are required")

    try:
        # Check if user already exists
        existing_user = await supabase.select("users")
        if existing_user.status_code == 200:
            users = existing_user.json()
            existing = next((u for u in users if u.get("chat_id") == location.chat_id), None)

            if existing:
                # Update existing user
                user_data = {}
                if location.city:
                    user_data["city"] = location.city.strip()
                if location.latitude is not None:
                    user_data["latitude"] = location.latitude
                if location.longitude is not None:
                    user_data["longitude"] = location.longitude

                # Update user
                async with httpx.AsyncClient() as client:
                    update_response = await client.patch(
                        f"{supabase.url}/rest/v1/users?id=eq.{existing['id']}",
                        headers=supabase.headers,
                        json=user_data
                    )

                print(f"Update response status: {update_response.status_code}")
                print(f"Update response text: {update_response.text}")
                print(f"Update user_data: {user_data}")
                print(f"Existing user ID: {existing['id']}")

                if update_response.status_code in [200, 204]:
                    # Parse the updated user data from response if available
                    updated_data = {}
                    try:
                        response_json = update_response.json()
                        if response_json and len(response_json) > 0:
                            updated_data = response_json[0]
                    except:
                        pass

                    return {
                        "message": f"Updated location for chat_id: {location.chat_id}",
                        "user_id": existing["id"],
                        "chat_id": location.chat_id,
                        "city": location.city or updated_data.get("city") or existing.get("city"),
                        "latitude": location.latitude or updated_data.get("latitude") or existing.get("latitude"),
                        "longitude": location.longitude or updated_data.get("longitude") or existing.get("longitude")
                    }
                else:
                    raise HTTPException(status_code=500, detail=f"Failed to update user: {update_response.text}")

        # Create new user record
        user_data = {
            "chat_id": location.chat_id
        }

        if location.city:
            user_data["city"] = location.city.strip()
        if location.latitude is not None:
            user_data["latitude"] = location.latitude
        if location.longitude is not None:
            user_data["longitude"] = location.longitude

        result = await supabase.insert("users", user_data)

        if result.status_code == 201:
            response_data = result.json()
            if response_data:
                return {
                    "message": f"Successfully registered location for chat_id: {location.chat_id}",
                    "user_id": response_data[0]["id"],
                    "chat_id": location.chat_id,
                    "city": location.city,
                    "latitude": location.latitude,
                    "longitude": location.longitude
                }
            else:
                raise HTTPException(status_code=500, detail="Failed to register location")
        else:
            raise HTTPException(status_code=500, detail=f"Failed to register location: {result.text}")

    except Exception as e:
        print(f"ERROR in register_location: {str(e)}")
        print(f"ERROR type: {type(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to register location: {str(e)}")

@app.delete("/delete_location/{chat_id}", response_model=dict)
async def delete_user_location(chat_id: int):
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")

    try:
        # Find the user by chat_id
        existing_user = await supabase.select("users")
        if existing_user.status_code == 200:
            users = existing_user.json()
            existing = next((u for u in users if u.get("chat_id") == chat_id), None)

            if existing:
                # Delete the user's location data
                async with httpx.AsyncClient() as client:
                    delete_response = await client.delete(
                        f"{supabase.url}/rest/v1/users?id=eq.{existing['id']}",
                        headers=supabase.headers
                    )

                if delete_response.status_code == 204:
                    return {
                        "message": f"Successfully deleted location for chat_id: {chat_id}",
                        "chat_id": chat_id,
                        "deleted_user_id": existing["id"]
                    }
                else:
                    raise HTTPException(status_code=500, detail=f"Failed to delete user location: {delete_response.text}")
            else:
                raise HTTPException(status_code=404, detail=f"User with chat_id {chat_id} not found")
        else:
            raise HTTPException(status_code=500, detail="Failed to fetch users from database")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete location: {str(e)}")

@app.post("/send_alerts", response_model=AlertResponse)
async def send_weather_alerts():
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")

    try:
        # Fetch all users from database
        users_result = await supabase.select("users")

        if users_result.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to fetch users from database")

        users = users_result.json()

        if not users:
            return AlertResponse(
                message="No users found in database",
                users_processed=0,
                alerts_sent=0
            )

        users_processed = len(users)
        alerts_sent = 0

        for user in users:
            try:
                # Get weather for user's city
                weather = await get_weather_for_city(user["city"])

                # Check if weather conditions warrant an alert
                if should_send_alert(weather):
                    # Log alert (in production, this would send to Telegram)
                    print(f"🚨 Weather Alert for {user['city']}:")
                    print(f"   Conditions: {weather['current']['description']}")
                    print(f"   Temperature: {weather['current']['temperature']}°C")
                    print(f"   User ID: {user['id']}")
                    alerts_sent += 1

            except Exception as e:
                print(f"Failed to process alerts for user {user['id']}: {str(e)}")
                continue

        return AlertResponse(
            message=f"Weather alerts processed for {users_processed} users",
            users_processed=users_processed,
            alerts_sent=alerts_sent
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send alerts: {str(e)}")

# Helper function to get weather for a city (reused from existing code)
async def get_weather_for_city(city: str) -> Dict[str, Any]:
    async with httpx.AsyncClient() as client:
        current_url = f"{OPENWEATHER_BASE_URL}/weather"
        current_params = {
            "q": city,
            "appid": OPENWEATHER_API_KEY,
            "units": "metric"
        }

        current_response = await client.get(current_url, params=current_params)
        if current_response.status_code != 200:
            raise Exception(f"Failed to fetch weather for {city}")

        current_data = current_response.json()

        return {
            "current": {
                "city": current_data["name"],
                "temperature": current_data["main"]["temp"],
                "description": current_data["weather"][0]["description"],
                "humidity": current_data["main"]["humidity"],
                "wind_speed": current_data["wind"]["speed"],
                "pressure": current_data["main"]["pressure"]
            }
        }

# Helper function to determine if weather warrants an alert
def should_send_alert(weather: Dict[str, Any]) -> bool:
    """
    Determine if weather conditions are poor enough to send an alert.
    Returns True if weather conditions are severe.
    """
    current = weather["current"]

    # Alert conditions (customize as needed)
    alert_conditions = [
        current["temperature"] < 0,  # Freezing temperatures
        current["temperature"] > 35,  # Extreme heat
        current["humidity"] > 85,  # High humidity
        current["wind_speed"] > 10,  # Strong winds
        "rain" in current["description"].lower(),
        "storm" in current["description"].lower(),
        "snow" in current["description"].lower(),
        "thunder" in current["description"].lower(),
        "hail" in current["description"].lower()
    ]

    return any(alert_conditions)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)