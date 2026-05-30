"""
MoStar MCP Gateway
Mediator. Requests. Cluster decides.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
import httpx
from fastapi import FastAPI, Request, HTTPException, Depends
from pydantic import BaseModel
from typing import Any, Dict

# Setup logging
LOG_FILE = Path("/home/idona/MoStar/_apps/grid/logs/mcp_gateway.jsonl")
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

def log_mcp_request(request_data: dict, status: str):
    log_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "mcp_request": request_data,
        "status": status
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(log_entry) + "\n")

app = FastAPI(title="MoStar MCP Gateway")

GRID_API_URL = "http://localhost:41010"

def verify_soulprint(request: Request):
    # Placeholder for Soulprint validation (Light gate)
    soulprint = request.headers.get("X-MoStar-Soulprint")
    return soulprint

def verify_thronelock(request: Request):
    # Placeholder for ThroneLock validation (Light gate)
    thronelock = request.headers.get("X-MoStar-ThroneLock")
    return thronelock

@app.post("/api/mcp/execute")
async def execute_mcp_tool(
    request: Request,
    soulprint: str = Depends(verify_soulprint),
    thronelock: str = Depends(verify_thronelock)
):
    try:
        mcp_data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # Log request arrival
    log_mcp_request(mcp_data, "received")
    
    # Route into Grid /api/propose (Mediator requests, Cluster decides)
    propose_payload = {
        "canon_input": json.dumps(mcp_data)
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{GRID_API_URL}/api/propose",
                json=propose_payload,
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()
            log_mcp_request(mcp_data, "proposed")
            return {"status": "proposed", "grid_response": data}
            
    except httpx.HTTPError as e:
        log_mcp_request(mcp_data, "failed")
        raise HTTPException(status_code=502, detail=f"Grid connection failed: {str(e)}")

@app.get("/api/health")
async def health():
    return {
        "service": "mcp-gateway",
        "status": "alive",
        "role": "mediator",
        "gates": ["soulprint_placeholder", "thronelock_placeholder"]
    }
