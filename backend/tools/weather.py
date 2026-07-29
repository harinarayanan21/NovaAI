import json
import logging
from langchain_core.tools import tool
import httpx

logger = logging.getLogger(__name__)

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"


@tool
def get_weather(city: str) -> str:
    """Get current weather for a city. Returns temperature, feels-like, humidity, weather description, and wind speed.

    Args:
        city: City name, e.g. "London" or "New York".

    Returns:
        JSON with weather data.
    """
    try:
        with httpx.Client(timeout=15) as client:
            geo_resp = client.get(
                GEOCODING_URL,
                params={"name": city, "count": 1, "language": "en"},
            )
            geo_data = geo_resp.json()

            if not geo_data.get("results"):
                return json.dumps({"success": False, "error": f"City not found: {city}"})

            loc = geo_data["results"][0]
            lat = loc["latitude"]
            lon = loc["longitude"]
            resolved_name = loc.get("name", city)
            country = loc.get("country", "")
            admin = loc.get("admin1", "")

            weather_resp = client.get(
                WEATHER_URL,
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "current": "temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m",
                    "timezone": "auto",
                },
            )
            weather_data = weather_resp.json()
            current = weather_data.get("current", {})

            WMO_CODES = {
                0: "Clear sky",
                1: "Mainly clear",
                2: "Partly cloudy",
                3: "Overcast",
                45: "Foggy",
                48: "Depositing rime fog",
                51: "Light drizzle",
                53: "Moderate drizzle",
                55: "Dense drizzle",
                61: "Slight rain",
                63: "Moderate rain",
                65: "Heavy rain",
                71: "Slight snow",
                73: "Moderate snow",
                75: "Heavy snow",
                77: "Snow grains",
                80: "Slight rain showers",
                81: "Moderate rain showers",
                82: "Violent rain showers",
                85: "Slight snow showers",
                86: "Heavy snow showers",
                95: "Thunderstorm",
                96: "Thunderstorm with slight hail",
                99: "Thunderstorm with heavy hail",
            }

            weather_code = current.get("weather_code", 0)
            description = WMO_CODES.get(weather_code, f"Code {weather_code}")

            location_parts = [resolved_name]
            if admin:
                location_parts.append(admin)
            if country:
                location_parts.append(country)

            result = {
                "success": True,
                "city": ", ".join(location_parts),
                "temperature": current.get("temperature_2m"),
                "feels_like": current.get("apparent_temperature"),
                "humidity": current.get("relative_humidity_2m"),
                "weather_description": description,
                "wind_speed": current.get("wind_speed_10m"),
                "units": {
                    "temperature": weather_data.get("current_units", {}).get("temperature_2m", "°C"),
                    "humidity": "%",
                    "wind_speed": weather_data.get("current_units", {}).get("wind_speed_10m", "km/h"),
                },
            }

            logger.info("Weather for %s: %s, %.1f°C", resolved_name, description, result["temperature"])
            return json.dumps(result)

    except httpx.TimeoutException:
        return json.dumps({"success": False, "error": "Weather service timed out"})
    except Exception as e:
        logger.error("Weather error: %s", str(e))
        return json.dumps({"success": False, "error": str(e)})
