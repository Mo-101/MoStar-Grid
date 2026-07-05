"""
MoStar MCP Gateway — Broker Client
Typed async HTTP client for the Grid API (Execution Broker at port 41010).
All MCP tools route through here. No privileged logic executes in this layer.
"""
import httpx

from mcp_gateway.config import GRID_API_URL, GRID_AUTH_DISABLED, MOSTAR_TOKEN


def _auth_headers() -> dict[str, str]:
    if GRID_AUTH_DISABLED:
        return {}
    if MOSTAR_TOKEN:
        return {"X-MoStar-Token": MOSTAR_TOKEN}
    return {}


async def grid_get(path: str, params: dict | None = None) -> dict:
    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.get(
            f"{GRID_API_URL}{path}",
            headers=_auth_headers(),
            params=params or {},
        )
        r.raise_for_status()
        return r.json()


async def grid_post(path: str, body: dict) -> dict:
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.post(
            f"{GRID_API_URL}{path}",
            json=body,
            headers=_auth_headers(),
        )
        r.raise_for_status()
        return r.json()
