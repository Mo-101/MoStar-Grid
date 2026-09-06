"""Read-only credential and dependency readiness checks.

Prints statuses only; credential values and credential-bearing URLs are never logged.
"""
from __future__ import annotations

import asyncio
import os
from pathlib import Path

import httpx
from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")


def result(name: str, ok: bool, detail: str) -> bool:
    print(f"{'PASS' if ok else 'FAIL'} {name}: {detail}")
    return ok


async def http_check(
    client: httpx.AsyncClient,
    name: str,
    method: str,
    url: str,
    *,
    headers: dict[str, str] | None = None,
    params: dict[str, str] | None = None,
    expected: set[int] = {200},
) -> bool:
    try:
        response = await client.request(method, url, headers=headers, params=params)
        return result(name, response.status_code in expected, f"HTTP {response.status_code}")
    except Exception as exc:
        return result(name, False, type(exc).__name__)


async def main() -> int:
    checks: list[bool] = []
    required = ("NEO4J_URI", "NEO4J_USER", "NEO4J_PASSWORD", "NEO4J_DATABASE", "MOSTAR_SESSION_TOKEN")
    for key in required:
        checks.append(result(f"env/{key}", bool(os.getenv(key, "").strip()), "configured" if os.getenv(key, "").strip() else "missing"))

    try:
        from neo4j import GraphDatabase

        driver = GraphDatabase.driver(
            os.environ["NEO4J_URI"],
            auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]),
            connection_timeout=8,
        )
        with driver.session(database=os.environ["NEO4J_DATABASE"]) as session:
            session.run("RETURN 1 AS ok").single(strict=True)
        driver.close()
        checks.append(result("neo4j", True, "authenticated query succeeded"))
    except Exception as exc:
        checks.append(result("neo4j", False, type(exc).__name__))

    try:
        import psycopg

        database_url = os.getenv("DATABASE_URL", "").strip()
        if not database_url:
            raise RuntimeError("DATABASE_URL is not configured")
        with psycopg.connect(database_url, connect_timeout=8) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        checks.append(result("postgres", True, "authenticated query succeeded"))
    except Exception as exc:
        checks.append(result("postgres", False, type(exc).__name__))

    timeout = httpx.Timeout(12.0)
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        if os.getenv("GROQ_API_KEY"):
            checks.append(await http_check(client, "groq", "GET", "https://api.groq.com/openai/v1/models", headers={"Authorization": f"Bearer {os.environ['GROQ_API_KEY']}"}))
        if os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_ANON_KEY"):
            checks.append(await http_check(client, "supabase", "GET", f"{os.environ['SUPABASE_URL'].rstrip('/')}/rest/v1/", headers={"apikey": os.environ["SUPABASE_ANON_KEY"], "Authorization": f"Bearer {os.environ['SUPABASE_ANON_KEY']}"}, expected={200, 404}))
        if os.getenv("MAPBOX_ACCESS_TOKEN"):
            checks.append(await http_check(client, "mapbox", "GET", "https://api.mapbox.com/styles/v1/mapbox/streets-v12", params={"access_token": os.environ["MAPBOX_ACCESS_TOKEN"]}))
        if os.getenv("OPENWEATHER_API_KEY"):
            checks.append(await http_check(client, "openweather", "GET", "https://api.openweathermap.org/data/2.5/weather", params={"q": "Nairobi", "appid": os.environ["OPENWEATHER_API_KEY"]}))
        if os.getenv("OLLAMA_BASE_URL"):
            headers = {"Authorization": f"Bearer {os.environ['OLLAMA_BEARER_TOKEN']}"} if os.getenv("OLLAMA_BEARER_TOKEN") else None
            checks.append(await http_check(client, "ollama", "GET", f"{os.environ['OLLAMA_BASE_URL'].rstrip('/')}/api/tags", headers=headers))

    passed = sum(checks)
    print(f"SUMMARY {passed}/{len(checks)} checks passed")
    return 0 if all(checks) else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
