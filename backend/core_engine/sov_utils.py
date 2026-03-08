# ═══════════════════════════════════════════════════════════════════
# MOSTAR GRID — SOVEREIGN UTILITIES
# The Flame Architect — MSTR-⚡ — MoStar Industries
# "Core primitives for sovereign execution."
# ═══════════════════════════════════════════════════════════════════

import os
import httpx
import asyncio
import platform
import subprocess
from typing import Dict, Any, List
from core_engine.grid_config import config

async def call_sovereign_model(prompt: str, model: str, system: str = "") -> Dict[str, Any]:
    """Execute inference on a local MoStar engine."""
    url = f"{config.OLLAMA_HOST}/api/chat"
    
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {
            "num_ctx": 8192,
            "temperature": 0.7
        }
    }

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            r = await client.post(url, json=payload)
            if r.status_code == 200:
                data = r.json()
                return {
                    "response": data.get("message", {}).get("content", ""),
                    "model": model,
                    "status": "success"
                }
            return {"error": f"Ollama error {r.status_code}", "status": "degraded"}
    except Exception as e:
        return {"error": str(e), "status": "offline"}

def get_runtime_info() -> Dict[str, Any]:
    """Retrieve system bodily integrity info."""
    info = {
        "os": platform.system(),
        "arch": platform.machine(),
        "python": platform.python_version(),
        "java": "missing"
    }
    
    try:
        # Check Java version
        res = subprocess.run(["java", "-version"], capture_output=True, text=True)
        if res.returncode == 0:
            # Java prints version to stderr
            version_line = res.stderr.splitlines()[0]
            info["java"] = version_line
    except:
        pass
        
    return info

def verify_java_runtime(required_version: int = 21) -> bool:
    """Rigid check for Java version compliance."""
    info = get_runtime_info()
    java_str = str(info["java"]).lower()
    return f"version \"{required_version}" in java_str or f" {required_version}." in java_str
