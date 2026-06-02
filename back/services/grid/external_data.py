"""
External Data Integrations — Weather, Flights, Health Surveillance
All credentials sourced from .env. Strict live-only, no mock fallbacks.

Active integrations:
  Weather  — MeteoSource (keyed, live) → OpenWeather (keyed) → Open-Meteo (free fallback)
  Flights  — FlightAware AeroAPI (keyed) — needs real token from flightaware.com/aeroapi/
  Health   — WHO GHO (open) + SORMAS (keyed, optional)
  Climate  — ECMWF (authenticated)
"""
import os
import httpx
import logging
from datetime import datetime, timezone, timedelta

logger = logging.getLogger("external_data")

# ── City / Airport config ─────────────────────────────────────────────────────
CITIES = {
    "Nairobi": {"lat": -1.286389,  "lon": 36.817223, "icao": "HKJK", "iata": "NBO"},
    "Kampala": {"lat":  0.313611,  "lon": 32.581111, "icao": "HUEN", "iata": "EBB"},
    "Lagos":   {"lat":  6.524379,  "lon":  3.379206, "icao": "DNMM", "iata": "LOS"},
}


# ── Weather ───────────────────────────────────────────────────────────────────

async def fetch_weather_data() -> dict:
    meteo_key   = os.getenv("VITE_METEO_SOURCE", "").strip()
    ow_key      = os.getenv("OPENWEATHER_API_KEY", "").strip()
    valid_meteo = len(meteo_key) >= 10
    valid_ow    = len(ow_key) >= 20 and ow_key not in ("YOUR_OPENWEATHER_API_KEY",)

    weather_info = {}

    async with httpx.AsyncClient(timeout=8.0) as client:
        for city, cfg in CITIES.items():
            try:
                # 1. MeteoSource — primary (live key confirmed)
                if valid_meteo:
                    url = (
                        f"https://www.meteosource.com/api/v1/free/point"
                        f"?lat={cfg['lat']}&lon={cfg['lon']}"
                        f"&sections=current&units=metric&key={meteo_key}"
                    )
                    resp = await client.get(url)
                    if resp.status_code == 200:
                        d = resp.json().get("current", {})
                        weather_info[city] = {
                            "temp":        d.get("temperature"),
                            "feels_like":  d.get("feels_like"),
                            "humidity":    d.get("humidity"),
                            "description": d.get("summary", d.get("icon", "—")),
                            "wind_kph":    round((d.get("wind", {}) or {}).get("speed", 0), 1),
                            "cloud_cover": d.get("cloud_cover"),
                            "source":      "meteosource",
                            "status":      "online",
                        }
                        continue

                # 2. OpenWeather fallback
                if valid_ow:
                    url = (
                        f"https://api.openweathermap.org/data/2.5/weather"
                        f"?q={city}&appid={ow_key}&units=metric"
                    )
                    resp = await client.get(url)
                    if resp.status_code == 200:
                        d = resp.json()
                        weather_info[city] = {
                            "temp":        d["main"]["temp"],
                            "feels_like":  d["main"].get("feels_like"),
                            "humidity":    d["main"].get("humidity"),
                            "description": d["weather"][0]["description"],
                            "wind_kph":    round(d.get("wind", {}).get("speed", 0) * 3.6, 1),
                            "source":      "openweather",
                            "status":      "online",
                        }
                        continue

                # 3. Open-Meteo — free, no key required
                url = (
                    f"https://api.open-meteo.com/v1/forecast"
                    f"?latitude={cfg['lat']}&longitude={cfg['lon']}"
                    f"&current=temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code"
                    f"&timezone=auto"
                )
                resp = await client.get(url)
                if resp.status_code == 200:
                    d = resp.json()["current"]
                    weather_info[city] = {
                        "temp":        d["temperature_2m"],
                        "humidity":    d.get("relative_humidity_2m"),
                        "wind_kph":    d.get("wind_speed_10m"),
                        "description": _wmo_description(d.get("weather_code", 0)),
                        "source":      "open-meteo",
                        "status":      "online",
                    }
                else:
                    weather_info[city] = {"status": "error", "code": resp.status_code}

            except Exception as e:
                logger.error(f"Weather fetch failed for {city}: {e}")
                weather_info[city] = {"status": "unavailable"}

    any_live = any(v.get("status") == "online" for v in weather_info.values())
    # Report whichever source actually responded
    sources = {v.get("source") for v in weather_info.values() if v.get("status") == "online"}
    provider = next(iter(sources), "open-meteo")
    return {
        "provider": provider,
        "status": "live" if any_live else "provider_unavailable",
        "live": any_live,
        "data": weather_info if any_live else None,
    }


def _wmo_description(code: int) -> str:
    wmo = {
        0: "clear sky", 1: "mainly clear", 2: "partly cloudy", 3: "overcast",
        45: "fog", 48: "icy fog", 51: "light drizzle", 53: "drizzle",
        61: "light rain", 63: "rain", 65: "heavy rain",
        71: "light snow", 73: "snow", 80: "rain showers", 95: "thunderstorm",
    }
    return wmo.get(code, f"code {code}")


# ── Flights ───────────────────────────────────────────────────────────────────

async def fetch_flight_data() -> dict:
    api_key = os.getenv("FLIGHTAWARE_API_KEY", "").strip()
    # "aeroapi" is the placeholder — reject it
    valid_key = api_key and api_key not in ("aeroapi", "", "YOUR_FLIGHTAWARE_KEY")

    if not valid_key:
        logger.warning(
            "FlightAware AeroAPI key is placeholder ('aeroapi'). "
            "Set FLIGHTAWARE_API_KEY to a real token from https://flightaware.com/aeroapi/"
        )
        return {
            "provider": "flightaware",
            "status": "awaiting_real_api_key",
            "live": False,
            "data": None,
            "note": "Set FLIGHTAWARE_API_KEY in .env — current value 'aeroapi' is the placeholder",
        }

    flight_info = {}
    async with httpx.AsyncClient(timeout=10.0) as client:
        headers = {"x-apikey": api_key}
        for city, cfg in CITIES.items():
            icao = cfg["icao"]
            try:
                url = f"https://aeroapi.flightaware.com/aeroapi/airports/{icao}/flights?max_pages=1&type=Airline"
                resp = await client.get(url, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    arrivals   = data.get("arrivals", [])
                    departures = data.get("departures", [])
                    details = []
                    if arrivals:
                        a = arrivals[0]
                        origin = a.get("origin", {}).get("code_iata", "?") if isinstance(a.get("origin"), dict) else "?"
                        details.append(f"Arr: {a.get('ident','?')} from {origin}")
                    if departures:
                        d = departures[0]
                        dest = d.get("destination", {}).get("code_iata", "?") if isinstance(d.get("destination"), dict) else "?"
                        details.append(f"Dep: {d.get('ident','?')} to {dest}")
                    flight_info[city] = {
                        "icao": icao,
                        "status": "online",
                        "summary": " | ".join(details) or "no active operations",
                    }
                elif resp.status_code == 401:
                    return {
                        "provider": "flightaware",
                        "status": "auth_failed",
                        "live": False,
                        "data": None,
                        "note": "AeroAPI key rejected — verify at flightaware.com/aeroapi",
                    }
                else:
                    flight_info[city] = {"status": "error", "code": resp.status_code}
            except Exception as e:
                logger.error(f"Flight fetch failed for {city} ({icao}): {e}")
                flight_info[city] = {"status": "unavailable"}

    any_live = any(v.get("status") == "online" for v in flight_info.values())
    return {
        "provider": "flightaware",
        "status": "live" if any_live else "provider_unavailable",
        "live": any_live,
        "data": flight_info if any_live else None,
    }


# ── Health Surveillance ───────────────────────────────────────────────────────

async def fetch_health_data() -> dict:
    """
    Aggregates public health signals from WHO GHO (open) and CDC (open).
    SORMAS is optional — set SORMAS_API_KEY to activate.
    """
    result = {"live": False, "sources": {}}

    async with httpx.AsyncClient(timeout=10.0) as client:

        # WHO GHO — disease burden indicator (open, no key)
        try:
            url = (
                "https://ghoapi.azureedge.net/api/WHOSIS_000001"
                "?$filter=SpatialDim eq 'KEN' or SpatialDim eq 'UGA' or SpatialDim eq 'NGA'"
                "&$orderby=TimeDim desc&$top=3"
            )
            resp = await client.get(url)
            if resp.status_code == 200:
                vals = resp.json().get("value", [])
                who_summary = {
                    v["SpatialDim"]: {
                        "indicator": "life_expectancy",
                        "value": v.get("NumericValue"),
                        "year": v.get("TimeDim"),
                    }
                    for v in vals
                }
                result["sources"]["who_gho"] = {
                    "status": "live",
                    "data": who_summary,
                }
                result["live"] = True
        except Exception as e:
            logger.error(f"WHO GHO fetch failed: {e}")
            result["sources"]["who_gho"] = {"status": "unavailable"}

        # SORMAS — optional, keyed
        sormas_url = os.getenv("SORMAS_API_KEY", "").strip()
        if sormas_url and sormas_url.startswith("http") and "sormas" in sormas_url:
            try:
                resp = await client.get(
                    f"{sormas_url.rstrip('/')}/api/cases/count",
                    timeout=6.0,
                )
                if resp.status_code == 200:
                    result["sources"]["sormas"] = {
                        "status": "live",
                        "data": {"active_cases": resp.json()},
                    }
                    result["live"] = True
                else:
                    result["sources"]["sormas"] = {"status": "error", "code": resp.status_code}
            except Exception as e:
                logger.warning(f"SORMAS fetch failed: {e}")
                result["sources"]["sormas"] = {"status": "unavailable"}

    return result


# ── Convenience: fetch all at once ────────────────────────────────────────────

async def fetch_all_external() -> dict:
    import asyncio
    weather, flights, health = await asyncio.gather(
        fetch_weather_data(),
        fetch_flight_data(),
        fetch_health_data(),
        return_exceptions=True,
    )
    return {
        "weather": weather if not isinstance(weather, Exception) else {"live": False, "status": "error"},
        "flights": flights if not isinstance(flights, Exception) else {"live": False, "status": "error"},
        "health":  health  if not isinstance(health,  Exception) else {"live": False, "status": "error"},
    }
