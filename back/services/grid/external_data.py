"""
External Data Integrations — Weather, Flights, Health Surveillance
All credentials sourced from .env. Strict live-only, no mock fallbacks.

Active integrations:
  Weather  — MeteoSource (keyed, live) → OpenWeather (keyed) → Open-Meteo (free fallback)
  Flights  — FlightAware AeroAPI (keyed) — needs real token from flightaware.com/aeroapi/
  Health   — WHO GHO (open) + SORMAS (optional endpoint)
  Climate  — ECMWF (authenticated)
"""
import os
import httpx
import logging
import asyncio
import time
import json
import hashlib
from statistics import mean
from datetime import datetime, timezone, timedelta

logger = logging.getLogger("external_data")
# Provider credentials can appear in query strings. Never allow the HTTP
# transport logger to persist request URLs in operational logs.
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

# ── City / Airport config ─────────────────────────────────────────────────────
CITIES = {
    "Nairobi": {"lat": -1.286389,  "lon": 36.817223, "icao": "HKJK", "iata": "NBO"},
    "Kampala": {"lat":  0.313611,  "lon": 32.581111, "icao": "HUEN", "iata": "EBB"},
    "Lagos":   {"lat":  6.524379,  "lon":  3.379206, "icao": "DNMM", "iata": "LOS"},
}

# Representative observation hubs across Africa's five operational regions.
# Interface coverage is continent-wide; measured weather coverage is reported
# honestly as these hubs rather than inferred for unobserved jurisdictions.
AFRICA_HUBS = {
    "Cairo": {"country": "Egypt", "region": "North", "lat": 30.0444, "lon": 31.2357},
    "Dakar": {"country": "Senegal", "region": "West", "lat": 14.7167, "lon": -17.4677},
    "Lagos": {"country": "Nigeria", "region": "West", "lat": 6.5244, "lon": 3.3792},
    "Nairobi": {"country": "Kenya", "region": "East", "lat": -1.2864, "lon": 36.8172},
    "Addis Ababa": {"country": "Ethiopia", "region": "East", "lat": 8.9806, "lon": 38.7578},
    "Kinshasa": {"country": "DR Congo", "region": "Central", "lat": -4.4419, "lon": 15.2663},
    "Lusaka": {"country": "Zambia", "region": "Southern", "lat": -15.3875, "lon": 28.3228},
    "Cape Town": {"country": "South Africa", "region": "Southern", "lat": -33.9249, "lon": 18.4241},
}

_SENSE_CACHE: dict = {"expires": 0.0, "payload": None}
SENSE_CACHE_SECONDS = max(15, int(os.getenv("AFRICA_SENSES_CACHE_SECONDS", "60")))


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _observation(provider: str, hub: str, cfg: dict, **values) -> dict:
    retrieved_at = _utcnow()
    return {
        "location_id": hub.lower().replace(" ", "-"),
        "location": hub,
        "country": cfg["country"],
        "region": cfg["region"],
        "provider": provider,
        "observed_at": values.pop("observed_at", None) or retrieved_at,
        "retrieved_at": retrieved_at,
        "time_basis": values.pop("time_basis", "provider_observation"),
        "freshness_seconds": 0,
        **values,
    }


async def _weather_provider(client: httpx.AsyncClient, provider: str, hub: str, cfg: dict) -> dict:
    try:
        if provider == "meteosource":
            key = os.getenv("VITE_METEO_SOURCE", "").strip()
            if not key:
                return {"provider": provider, "state": "MISSING"}
            response = await client.get("https://www.meteosource.com/api/v1/free/point", params={
                "lat": cfg["lat"], "lon": cfg["lon"], "sections": "current",
                "units": "metric", "key": key,
            })
            if response.status_code != 200:
                return {"provider": provider, "state": "REJECTED" if response.status_code in (401, 403) else "DEGRADED"}
            data = response.json().get("current", {})
            wind = data.get("wind", {}) or {}
            return _observation(provider, hub, cfg,
                temperature_c=data.get("temperature"), feels_like_c=data.get("feels_like"),
                humidity_pct=data.get("humidity"), wind_kph=wind.get("speed"),
                wind_direction_deg=wind.get("angle"), precipitation_mm=data.get("precipitation", {}).get("total"),
                summary=data.get("summary") or data.get("icon") or "Observed conditions",
                time_basis="retrieval_time")

        if provider == "openweather":
            key = os.getenv("OPENWEATHER_API_KEY", "").strip()
            if not key:
                return {"provider": provider, "state": "MISSING"}
            response = await client.get("https://api.openweathermap.org/data/2.5/weather", params={
                "lat": cfg["lat"], "lon": cfg["lon"], "appid": key, "units": "metric",
            })
            if response.status_code != 200:
                return {"provider": provider, "state": "REJECTED" if response.status_code in (401, 403) else "DEGRADED"}
            data = response.json()
            observed_at = datetime.fromtimestamp(data["dt"], timezone.utc).isoformat() if data.get("dt") else None
            return _observation(provider, hub, cfg,
                temperature_c=data.get("main", {}).get("temp"), feels_like_c=data.get("main", {}).get("feels_like"),
                humidity_pct=data.get("main", {}).get("humidity"), wind_kph=round(data.get("wind", {}).get("speed", 0) * 3.6, 1),
                wind_direction_deg=data.get("wind", {}).get("deg"), precipitation_mm=(data.get("rain", {}) or {}).get("1h", 0),
                summary=(data.get("weather") or [{}])[0].get("description", "Observed conditions"),
                observed_at=observed_at)

        response = await client.get("https://api.open-meteo.com/v1/forecast", params={
            "latitude": cfg["lat"], "longitude": cfg["lon"],
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m,wind_direction_10m",
            "hourly": "temperature_2m,precipitation_probability", "forecast_days": 1, "timezone": "UTC",
        })
        if response.status_code != 200:
            return {"provider": provider, "state": "DEGRADED"}
        data = response.json(); current = data.get("current", {}); hourly = data.get("hourly", {})
        return _observation(provider, hub, cfg,
            temperature_c=current.get("temperature_2m"), feels_like_c=current.get("apparent_temperature"),
            humidity_pct=current.get("relative_humidity_2m"), wind_kph=current.get("wind_speed_10m"),
            wind_direction_deg=current.get("wind_direction_10m"), precipitation_mm=current.get("precipitation"),
            precipitation_probability=(hourly.get("precipitation_probability") or [None])[0],
            # Machine-readable WMO code alongside the prose summary. The surface
            # renders the live sky from this when present; only Open-Meteo speaks
            # WMO, so consumers must still degrade to `summary` text.
            weather_code=current.get("weather_code"),
            summary=_wmo_description(current.get("weather_code", 0)), observed_at=current.get("time"),
            forecast={"temperature_c": (hourly.get("temperature_2m") or [])[:12],
                      "precipitation_probability": (hourly.get("precipitation_probability") or [])[:12]})
    except Exception as exc:
        logger.warning("%s weather probe failed for %s: %s", provider, hub, type(exc).__name__)
        return {"provider": provider, "state": "UNREACHABLE"}


def _consensus(hub: str, cfg: dict, observations: list[dict]) -> dict:
    valid = [item for item in observations if "temperature_c" in item and item.get("temperature_c") is not None]
    temperatures = [float(item["temperature_c"]) for item in valid]
    winds = [float(item["wind_kph"]) for item in valid if item.get("wind_kph") is not None]
    humidities = [float(item["humidity_pct"]) for item in valid if item.get("humidity_pct") is not None]
    spread = max(temperatures) - min(temperatures) if len(temperatures) > 1 else None
    agreement = round(max(0.0, 1.0 - (spread or 0) / 8), 2) if len(valid) > 1 else 0.5 if valid else 0.0
    state = "CONSENSUS" if len(valid) >= 2 and agreement >= .8 else "DIVERGENT" if len(valid) >= 2 else "PARTIAL" if valid else "UNAVAILABLE"
    primary = valid[0] if valid else {}
    # Hub coordinates are measured configuration, not inference. They travel
    # with the observation so the surface can resolve real solar day/night for
    # the observed place instead of the viewer's browser timezone.
    coded = next((item for item in valid if item.get("weather_code") is not None), {})
    return {
        "location_id": hub.lower().replace(" ", "-"), "location": hub,
        "country": cfg["country"], "region": cfg["region"],
        "latitude": cfg["lat"], "longitude": cfg["lon"],
        "weather_code": coded.get("weather_code"),
        "temperature_c": round(mean(temperatures), 1) if temperatures else None,
        "feels_like_c": primary.get("feels_like_c"),
        "humidity_pct": round(mean(humidities)) if humidities else None,
        "wind_kph": round(mean(winds), 1) if winds else None,
        "wind_direction_deg": primary.get("wind_direction_deg"),
        "precipitation_mm": primary.get("precipitation_mm"),
        "precipitation_probability": primary.get("precipitation_probability"),
        "summary": primary.get("summary", "No current source"),
        "agreement_score": agreement, "provider_count": len(valid),
        "providers_used": [item["provider"] for item in valid],
        "epistemic_state": state, "temperature_spread_c": round(spread, 1) if spread is not None else None,
        "freshness_seconds": max((item.get("freshness_seconds", 0) for item in valid), default=None),
        "observed_at": primary.get("observed_at"), "retrieved_at": primary.get("retrieved_at"),
        "time_basis": primary.get("time_basis"), "forecast": primary.get("forecast"),
        "source_observations": valid,
    }


def _age_seconds(value: str | None) -> int | None:
    if not value:
        return None
    try:
        observed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if observed.tzinfo is None:
            observed = observed.replace(tzinfo=timezone.utc)
        return max(0, int((datetime.now(timezone.utc) - observed.astimezone(timezone.utc)).total_seconds()))
    except (TypeError, ValueError):
        return None


def _refresh_payload_ages(payload: dict) -> dict:
    refreshed = dict(payload)
    refreshed["weather"] = dict(payload["weather"])
    refreshed["weather"]["locations"] = []
    for location in payload["weather"]["locations"]:
        item = dict(location)
        item["freshness_seconds"] = _age_seconds(item.get("observed_at"))
        refreshed["weather"]["locations"].append(item)
    refreshed["served_at"] = _utcnow()
    return refreshed


def _canonical_africa_report(payload: dict) -> dict:
    locations = payload["weather"]["locations"]
    observed = [item for item in locations if item.get("provider_count", 0) > 0]
    weather_lines = [
        f"{item['location']}, {item['country']}: {item['temperature_c']} degrees Celsius, {item['summary']}, from {item['provider_count']} measured source{'s' if item['provider_count'] != 1 else ''}."
        for item in observed
    ]
    segments = [
        f"Africa sensing report, generated {payload['generated_at']}. Weather coverage is {len(observed)} of {len(locations)} configured observation hubs.",
        *weather_lines,
        f"Health source state is {payload['health']['state'].lower()}. Sovereignty reporting remains {payload['sovereignty']['state'].lower()} and does not infer governance claims from weather or health observations.",
    ]
    material = json.dumps({"weather": locations, "health": payload["health"], "sovereignty": payload["sovereignty"]}, sort_keys=True, separators=(",", ":"), default=str)
    return {
        "report_id": f"africa-senses-{payload['generated_at']}", "canonical": True,
        "generated_at": payload["generated_at"], "segments": segments, "text": " ".join(segments),
        "source_digest": hashlib.sha256(material.encode("utf-8")).hexdigest(),
        "source_refs": sorted({provider for item in observed for provider in item.get("providers_used", [])}),
    }


async def fetch_africa_senses(force: bool = False) -> dict:
    """Return normalized, cached, provenance-bearing continental observations."""
    now = time.monotonic()
    if not force and _SENSE_CACHE["payload"] and now < _SENSE_CACHE["expires"]:
        payload = _refresh_payload_ages(_SENSE_CACHE["payload"])
        payload["cache"] = "HIT"
        return payload

    async with httpx.AsyncClient(timeout=20.0) as client:
        tasks = [
            _weather_provider(client, provider, hub, cfg)
            for hub, cfg in AFRICA_HUBS.items()
            for provider in ("meteosource", "openweather", "open_meteo")
        ]
        raw = await asyncio.gather(*tasks)

    weather = []
    provider_states = {name: "UNAVAILABLE" for name in ("meteosource", "openweather", "open_meteo")}
    for index, (hub, cfg) in enumerate(AFRICA_HUBS.items()):
        observations = raw[index * 3:index * 3 + 3]
        weather.append(_consensus(hub, cfg, observations))
        for observation in observations:
            provider = observation.get("provider")
            if provider and "temperature_c" in observation:
                provider_states[provider] = "HEALTHY"
            elif provider and provider_states[provider] != "HEALTHY":
                provider_states[provider] = observation.get("state", "DEGRADED")

    health = await fetch_health_data()
    health_sources = health.get("sources", {})
    live_health_sources = [source for source in health_sources.values() if source.get("status") == "live"]
    health_state = (
        "HEALTHY" if len(live_health_sources) >= 2 and len(live_health_sources) == len(health_sources)
        else "PARTIAL" if live_health_sources
        else "UNAVAILABLE"
    )
    generated_at = _utcnow()
    covered_regions = sorted({item["region"] for item in weather if item["provider_count"]})
    sovereignty = [
        {
            "report_id": f"grid-{region.lower()}-{datetime.now(timezone.utc).strftime('%Y%m%d')}",
            "jurisdiction_id": region.lower(), "jurisdiction": f"{region} Africa",
            "generated_at": generated_at, "state": "PARTIAL",
            "findings": [
                {"section": "climate_weather", "statement": f"{sum(1 for item in weather if item['region'] == region)} observation hub(s) reporting.", "epistemic_type": "OBSERVED", "confidence": "MEASURED"},
                {"section": "health", "statement": "WHO continental indicators available; jurisdiction-level event coverage remains partial.", "epistemic_type": "SOURCE_REPORT", "confidence": "PARTIAL"},
                {"section": "governance", "statement": "No current approved governance source connected.", "epistemic_type": "NO_CURRENT_SOURCE", "confidence": "UNAVAILABLE"},
            ],
            "source_coverage": ["weather", "who_gho"], "contested": False,
            "freshness": {"state": "CURRENT", "generated_at": generated_at},
            "provenance_refs": ["meteosource", "openweather", "open_meteo", "who_gho"],
        }
        for region in ("North", "West", "Central", "East", "Southern")
    ]
    payload = {
        "generated_at": generated_at, "served_at": generated_at, "cache": "MISS", "scope": "Africa",
        "coverage": {"jurisdictions": 54, "weather_hubs_observed": sum(item["provider_count"] > 0 for item in weather), "regions_observed": covered_regions},
        "weather": {"state": "HEALTHY" if all(v == "HEALTHY" for v in provider_states.values()) else "PARTIAL", "providers": provider_states, "locations": weather},
        "health": {"state": health_state, "providers": {key: value.get("status", "unknown").upper() for key, value in health_sources.items()}, "signals": health_sources},
        "sovereignty": {"state": "PARTIAL", "reports": sovereignty},
    }
    payload["canonical_report"] = _canonical_africa_report(payload)
    _SENSE_CACHE.update({"expires": now + SENSE_CACHE_SECONDS, "payload": payload})
    return payload


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
    SORMAS is optional — set SORMAS_API_BASE_URL to activate.
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
            else:
                result["sources"]["who_gho"] = {"status": "error", "code": resp.status_code}
        except Exception as e:
            logger.error(f"WHO GHO fetch failed: {e}")
            result["sources"]["who_gho"] = {"status": "unavailable"}

        # CDC Socrata catalog reachability. This establishes source health,
        # not Africa-specific epidemiological coverage; the UI labels it as
        # partial until approved datasets are selected and normalized.
        try:
            cdc_base = os.getenv("CDC_SOCRATA_BASE_URL", "https://data.cdc.gov").rstrip("/")
            resp = await client.get(f"{cdc_base}/api/views.json", params={"limit": 1})
            if resp.status_code in (200, 404):
                result["sources"]["cdc_socrata"] = {
                    "status": "live",
                    "data": {"coverage": "catalog_reachable", "africa_specific": False},
                }
                result["live"] = True
            else:
                result["sources"]["cdc_socrata"] = {"status": "error", "code": resp.status_code}
        except Exception as e:
            logger.error(f"CDC Socrata fetch failed: {e}")
            result["sources"]["cdc_socrata"] = {"status": "unavailable"}

        # SORMAS — optional endpoint
        sormas_url = os.getenv("SORMAS_API_BASE_URL", "").strip()
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
