"""
External Data Integrations — Weather and Flights
Sovereign credentials check, strict ground-truth enforcement. No mock fallbacks.
"""
import os
import httpx
import logging

logger = logging.getLogger("external_data")

async def fetch_weather_data() -> dict:
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key or len(api_key.strip()) < 10 or api_key == "YOUR_OPENWEATHER_API_KEY":
        logger.warning("OpenWeather API key missing or invalid placeholder.")
        return {
            "provider": "openweather",
            "status": "blocked_missing_credentials",
            "live": False,
            "data": None
        }

    cities = ["Nairobi", "Kampala", "Lagos"]
    weather_info = {}
    
    async with httpx.AsyncClient(timeout=8.0) as client:
        for city in cities:
            try:
                url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    temp = data.get("main", {}).get("temp")
                    desc = data.get("weather", [{}])[0].get("description", "clear sky")
                    weather_info[city] = {
                        "temp": temp,
                        "description": desc,
                        "status": "online"
                    }
                else:
                    weather_info[city] = {
                        "status": "error",
                        "code": resp.status_code
                    }
            except Exception as e:
                logger.error(f"Failed to fetch weather for {city}: {e}")
                weather_info[city] = {
                    "status": "unavailable",
                    "error": str(e)
                }

    # Determine overall status
    any_success = any(info.get("status") == "online" for info in weather_info.values())
    
    return {
        "provider": "openweather",
        "status": "live" if any_success else "provider_unavailable",
        "live": any_success,
        "data": weather_info if any_success else None
    }


async def fetch_flight_data() -> dict:
    api_key = os.getenv("FLIGHTAWARE_API_KEY")
    if not api_key or api_key.strip() == "aeroapi" or api_key.strip() == "":
        logger.warning("FlightAware API key missing or default placeholder 'aeroapi'.")
        return {
            "provider": "flightaware",
            "status": "blocked_missing_credentials",
            "live": False,
            "data": None
        }

    airports = {
        "Nairobi": "HKJK",
        "Kampala": "HUEN",
        "Lagos": "DNMM"
    }
    flight_info = {}

    async with httpx.AsyncClient(timeout=8.0) as client:
        headers = {"x-apikey": api_key}
        for city, icao in airports.items():
            try:
                # AeroAPI v3 arrivals & departures URL
                url = f"https://aeroapi.flightaware.com/aeroapi/airports/{icao}/flights?limit=2"
                resp = await client.get(url, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    arrivals = data.get("arrivals", [])
                    departures = data.get("departures", [])
                    
                    details = []
                    if arrivals:
                        arr = arrivals[0]
                        ident = arr.get("ident", "Unknown")
                        origin = arr.get("origin", {}).get("code", "Unknown") if isinstance(arr.get("origin"), dict) else arr.get("origin", "Unknown")
                        details.append(f"Arrival: {ident} from {origin}")
                    if departures:
                        dep = departures[0]
                        ident = dep.get("ident", "Unknown")
                        dest = dep.get("destination", {}).get("code", "Unknown") if isinstance(dep.get("destination"), dict) else dep.get("destination", "Unknown")
                        details.append(f"Departure: {ident} to {dest}")
                        
                    flight_info[city] = {
                        "status": "online",
                        "icao": icao,
                        "summary": " | ".join(details) if details else "no active operations"
                    }
                else:
                    flight_info[city] = {
                        "status": "error",
                        "code": resp.status_code
                    }
            except Exception as e:
                logger.error(f"Failed to fetch flights for {city} ({icao}): {e}")
                flight_info[city] = {
                    "status": "unavailable",
                    "error": str(e)
                }

    any_success = any(info.get("status") == "online" for info in flight_info.values())
    
    return {
        "provider": "flightaware",
        "status": "live" if any_success else "provider_unavailable",
        "live": any_success,
        "data": flight_info if any_success else None
    }
