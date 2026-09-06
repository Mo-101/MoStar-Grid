"""Read-only census of MoStar Grid external senses. Never prints secrets or URLs."""
from __future__ import annotations

import asyncio
import json
import os
import socket
from pathlib import Path
from urllib.parse import urlparse

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

PLACEHOLDERS = ("add here", "your_", "your-", "replace", "changeme", "placeholder", "todo", "nah")
rows: list[dict[str, str]] = []


def value(name: str) -> str:
    return os.getenv(name, "").strip()


def usable(name: str) -> bool:
    raw = value(name)
    return bool(raw) and not any(marker in raw.lower() for marker in PLACEHOLDERS)


def mark(sense: str, provider: str, status: str, detail: str, keys: str) -> None:
    rows.append({"sense": sense, "provider": provider, "status": status, "detail": detail, "keys": keys})
    print(f"{status:12} {sense:12} {provider:20} {detail}")


async def probe(
    client: httpx.AsyncClient,
    sense: str,
    provider: str,
    url: str,
    keys: str,
    *,
    headers: dict[str, str] | None = None,
    params: dict[str, str] | None = None,
    accepted: set[int] = {200},
) -> None:
    try:
        response = await client.get(url, headers=headers, params=params)
        status = "WORKING" if response.status_code in accepted else "REJECTED" if response.status_code in {401, 403} else "NON_WORKING"
        mark(sense, provider, status, f"HTTP {response.status_code}", keys)
    except (httpx.ConnectError, httpx.ConnectTimeout, socket.gaierror):
        mark(sense, provider, "UNREACHABLE", "connection/DNS failed", keys)
    except httpx.TimeoutException:
        mark(sense, provider, "UNREACHABLE", "timed out", keys)
    except Exception as exc:
        mark(sense, provider, "NON_WORKING", type(exc).__name__, keys)


async def main() -> int:
    timeout = httpx.Timeout(15.0)
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        # Graph and databases
        try:
            from neo4j import GraphDatabase
            driver = GraphDatabase.driver(value("NEO4J_URI"), auth=(value("NEO4J_USER"), value("NEO4J_PASSWORD")), connection_timeout=8)
            with driver.session(database=value("NEO4J_DATABASE")) as session:
                session.run("RETURN 1").single(strict=True)
            driver.close()
            mark("memory", "Neo4j", "WORKING", "authenticated query", "NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, NEO4J_DATABASE")
        except Exception as exc:
            mark("memory", "Neo4j", "NON_WORKING", type(exc).__name__, "NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, NEO4J_DATABASE")

        if usable("DATABASE_URL"):
            try:
                import psycopg
                with psycopg.connect(value("DATABASE_URL"), connect_timeout=8) as connection:
                    with connection.cursor() as cursor:
                        cursor.execute("SELECT 1"); cursor.fetchone()
                mark("governance", "Sovereign Postgres", "WORKING", "authenticated query", "DATABASE_URL")
            except Exception as exc:
                mark("governance", "Sovereign Postgres", "NON_WORKING", type(exc).__name__, "DATABASE_URL")
        else:
            mark("governance", "Sovereign Postgres", "MISSING", "credential absent", "DATABASE_URL")

        if usable("NEON_DATABASE_URL"):
            try:
                import psycopg
                with psycopg.connect(value("NEON_DATABASE_URL"), connect_timeout=8) as connection:
                    with connection.cursor() as cursor:
                        cursor.execute("SELECT 1"); cursor.fetchone()
                mark("data", "Neon Postgres", "WORKING", "authenticated query", "NEON_DATABASE_URL")
            except Exception as exc:
                mark("data", "Neon Postgres", "NON_WORKING", type(exc).__name__, "NEON_DATABASE_URL")
        if usable("NEON_JWKS_URL"):
            await probe(client, "identity", "Neon JWKS", value("NEON_JWKS_URL"), "NEON_JWKS_URL")
        if usable("SUPABASE_URL") and usable("SUPABASE_ANON_KEY"):
            await probe(
                client, "data", "Supabase REST", f"{value('SUPABASE_URL').rstrip('/')}/rest/v1/",
                "SUPABASE_URL, SUPABASE_ANON_KEY, NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_ANON_KEY",
                headers={"apikey": value("SUPABASE_ANON_KEY"), "Authorization": f"Bearer {value('SUPABASE_ANON_KEY')}"},
                accepted={200, 404},
            )
        else: mark("data", "Supabase REST", "MISSING", "URL/key absent", "SUPABASE_URL, SUPABASE_ANON_KEY")

        # Intelligence
        if usable("GROQ_API_KEY"):
            await probe(client, "intelligence", "Groq", "https://api.groq.com/openai/v1/models", "GROQ_API_KEY", headers={"Authorization": f"Bearer {value('GROQ_API_KEY')}"})
        else: mark("intelligence", "Groq", "MISSING", "credential absent/placeholder", "GROQ_API_KEY")
        if usable("OLLAMA_BASE_URL"):
            headers = {"Authorization": f"Bearer {value('OLLAMA_BEARER_TOKEN')}"} if usable("OLLAMA_BEARER_TOKEN") else None
            if usable("CF_ACCESS_CLIENT_ID") and usable("CF_ACCESS_CLIENT_SECRET"):
                headers = headers or {}
                headers.update({"CF-Access-Client-Id": value("CF_ACCESS_CLIENT_ID"), "CF-Access-Client-Secret": value("CF_ACCESS_CLIENT_SECRET")})
            await probe(client, "intelligence", "Ollama/DCX", f"{value('OLLAMA_BASE_URL').rstrip('/')}/api/tags", "OLLAMA_BASE_URL, OLLAMA_BEARER_TOKEN, DCX0_MODEL, DCX1_MODEL, DCX2_MODEL", headers=headers)

        # Weather and climate
        if usable("VITE_METEO_SOURCE"):
            await probe(client, "weather", "MeteoSource", "https://www.meteosource.com/api/v1/free/point", "VITE_METEO_SOURCE", params={"lat": "-1.286389", "lon": "36.817223", "sections": "current", "units": "metric", "key": value("VITE_METEO_SOURCE")})
        else: mark("weather", "MeteoSource", "MISSING", "credential absent/placeholder", "VITE_METEO_SOURCE")
        if usable("OPENWEATHER_API_KEY"):
            await probe(client, "weather", "OpenWeather", "https://api.openweathermap.org/data/2.5/weather", "OPENWEATHER_API_KEY, VITE_OPENWEATHER_API", params={"q": "Nairobi", "appid": value("OPENWEATHER_API_KEY"), "units": "metric"})
        else: mark("weather", "OpenWeather", "MISSING", "credential absent/placeholder", "OPENWEATHER_API_KEY")
        if usable("VITE_AERIS_CLIENT_ID") and usable("VITE_AERIS_CLIENT_SECRET"):
            await probe(client, "weather", "Aeris", "https://api.aerisapi.com/observations/nairobi,ke", "VITE_AERIS_CLIENT_ID, VITE_AERIS_CLIENT_SECRET", params={"client_id": value("VITE_AERIS_CLIENT_ID"), "client_secret": value("VITE_AERIS_CLIENT_SECRET"), "limit": "1"})
        else: mark("weather", "Aeris", "MISSING", "credential absent/placeholder", "VITE_AERIS_CLIENT_ID, VITE_AERIS_CLIENT_SECRET")
        await probe(client, "weather", "Open-Meteo", "https://api.open-meteo.com/v1/forecast", "none", params={"latitude": "-1.286389", "longitude": "36.817223", "current": "temperature_2m"})

        # Maps and earth observation
        if usable("MAPBOX_ACCESS_TOKEN"):
            await probe(client, "geospatial", "Mapbox", "https://api.mapbox.com/styles/v1/mapbox/streets-v12", "MAPBOX_ACCESS_TOKEN, NEXT_PUBLIC_MAPBOX_TOKEN", params={"access_token": value("MAPBOX_ACCESS_TOKEN")})
        else: mark("geospatial", "Mapbox", "MISSING", "credential absent/placeholder", "MAPBOX_ACCESS_TOKEN")
        if usable("CESIUM_ION_TOKEN"):
            await probe(client, "geospatial", "Cesium ion", "https://api.cesium.com/v1/me", "CESIUM_ION_TOKEN", headers={"Authorization": f"Bearer {value('CESIUM_ION_TOKEN')}"})
        else: mark("geospatial", "Cesium ion", "MISSING", "credential absent/placeholder", "CESIUM_ION_TOKEN")

        # Health signals
        await probe(client, "health", "WHO GHO", "https://ghoapi.azureedge.net/api/WHOSIS_000001?$top=1", "WHO_GHO_BASE_URL")
        await probe(client, "health", "CDC Socrata", f"{value('CDC_SOCRATA_BASE_URL').rstrip('/')}/api/views.json" if usable("CDC_SOCRATA_BASE_URL") else "https://data.cdc.gov/api/views.json", "CDC_SOCRATA_BASE_URL", accepted={200, 400, 404})
        if usable("SORMAS_API_BASE_URL"):
            await probe(client, "health", "SORMAS", f"{value('SORMAS_API_BASE_URL').rstrip('/')}/api/cases/count", "SORMAS_API_BASE_URL")
        else: mark("health", "SORMAS", "MISSING", "endpoint absent/placeholder", "SORMAS_API_BASE_URL")
        if usable("NPHCDA_FHIR_BASE_URL"):
            await probe(client, "health", "NPHCDA FHIR", f"{value('NPHCDA_FHIR_BASE_URL').rstrip('/')}/metadata", "NPHCDA_FHIR_BASE_URL", accepted={200, 401, 403})
        else: mark("health", "NPHCDA FHIR", "MISSING", "endpoint absent/placeholder", "NPHCDA_FHIR_BASE_URL")

        # Aviation / vision / local services
        if usable("FLIGHTAWARE_API_KEY"):
            await probe(client, "aviation", "FlightAware", "https://aeroapi.flightaware.com/aeroapi/airports/HKJK/flights", "FLIGHTAWARE_API_KEY", headers={"x-apikey": value("FLIGHTAWARE_API_KEY")}, params={"max_pages": "1"})
        else: mark("aviation", "FlightAware", "MISSING", "credential absent/placeholder", "FLIGHTAWARE_API_KEY")
        for provider, sense, env_name, suffix in [
            ("Grid API", "core", "MCP_CLUSTER_API_URL", "/api/live"),
            ("MCP Gateway", "coordination", "MCP_GATEWAY_URL", "/health"),
            ("YOLO", "vision", "YOLO_API_URL", "/health"),
        ]:
            if usable(env_name): await probe(client, sense, provider, f"{value(env_name).rstrip('/')}{suffix}", env_name, accepted={200, 404})
            else: mark(sense, provider, "MISSING", "endpoint absent", env_name)

        front_env: dict[str, str] = {}
        for line in (ROOT / "front" / "app" / ".env").read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                key, raw = line.split("=", 1); front_env[key] = raw.strip().strip('"')
        for provider, sense, env_name, suffix in [
            ("Voice", "hearing", "VITE_MOSTAR_VOICE_URL", "/health"),
            ("Personality", "interpretation", "VITE_PERSONALITY_ENGINE_URL", "/api/health"),
            ("DCX Trinity", "intelligence", "VITE_DCX_TRINITY_URL", "/api/health"),
        ]:
            endpoint = front_env.get(env_name, "").strip()
            if endpoint: await probe(client, sense, provider, f"{endpoint.rstrip('/')}{suffix}", env_name, accepted={200, 404})
            else: mark(sense, provider, "MISSING", "endpoint absent", env_name)

    # Configuration-only groups: syntactically present, but no safe provider identity endpoint.
    for provider, keys in [
        ("Cloudflare Access", "CF_ACCESS_CLIENT_ID, CF_ACCESS_CLIENT_SECRET"),
        ("Stack Auth", "VITE_PUBLIC_STACK_PROJECT_ID, VITE_PUBLIC_STACK_PUBLISHABLE_CLIENT_KEY, STACK_SECRET_SERVER_KEY"),
        ("ECMWF/CDS", "VITE_ECMWF_URL, VITE_ECMWF_KEY, VITE_ECMWF_EMAIL, VITE_CDS_URL, VITE_CDS_KEY"),
        ("Supabase admin", "SUPABASE_SERVICE_ROLE_KEY, SUPABASE_JWT_SECRET"),
        ("Vercel OIDC", "VERCEL_OIDC_TOKEN"),
        ("DNS declarations", "DNS_ZONE, DNS_SOA, DNS_A_MSG, DNS_NS_1, DNS_NS_2, DNS_NS_3, DNS_MX_1, DNS_MX_2, DNS_TXT_DMARC, DNS_TXT_SPF, DNS_TXT_DKIM"),
    ]:
        names = [item.strip() for item in keys.split(",")]
        status = "CONFIG_ONLY" if all(usable(name) for name in names) else "MISSING"
        mark("config", provider, status, "present; no safe standalone auth probe" if status == "CONFIG_ONLY" else "one or more values absent", keys)

    report = ROOT / "logs" / "africa_senses_readiness.json"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    working = sum(row["status"] == "WORKING" for row in rows)
    print(f"SUMMARY {working}/{len(rows)} providers working; report={report.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
