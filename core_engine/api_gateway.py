#!/usr/bin/env python3
"""
🧠 MoStar Grid API Gateway
--------------------------
Bridges Ollama reasoning, Neo4j logging, and Voice synthesis into one unified interface.
"""

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import os
from fastapi import FastAPI, Request, Form
from fastapi.responses import JSONResponse, FileResponse
from dotenv import load_dotenv
from gtts import gTTS
from pathlib import Path
from core_engine.mostar_moments_log import log_mostar_moment
from core_engine.voice_integration import MostarVoice
from fastapi import APIRouter
from pydantic import BaseModel
from core_engine.orchestrator import route_query, fetch_neo4j_context

# === API routers ===
router = APIRouter()
knowledge_router = APIRouter()

# === Load environment variables ===
load_dotenv()

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3:4b")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
NEO4J_URI = os.getenv("NEO4J_URI", "")
TTS_LANG = os.getenv("TTS_LANG", "en")
SYSTEM_PROMPT = os.getenv("SYSTEM_PROMPT", "You are REMOSTAR, a distributed MoStar consciousness.")

# === Core setup ===
app = FastAPI(title="MoStar Grid API", version="1.0.0")
mv = MostarVoice(lang=TTS_LANG)
audio_dir = Path("data/voice_cache")
audio_dir.mkdir(parents=True, exist_ok=True)


def _check_neo4j_connectivity() -> str:
    """Check Neo4j connectivity and return status."""
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(
            os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            auth=(os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD", ""))
        )
        driver.verify_connectivity()
        driver.close()
        return "online"
    except:
        return "offline"


async def _check_ollama_connectivity() -> str:
    """Check Ollama connectivity and return status."""
    try:
        import httpx
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get(f"{OLLAMA_HOST}/api/tags")
            if resp.status_code == 200:
                return "online"
    except:
        pass
    return "offline"


def _calculate_dcx_status(ollama_state: str, neo4j_state: str) -> tuple[str, str, str]:
    """Calculate DCX layer statuses based on service states."""
    dcx0_status = "online" if ollama_state == "online" else "offline"
    dcx1_status = "online" if neo4j_state == "online" else "offline"
    
    if ollama_state == "online" and neo4j_state == "online":
        dcx2_status = "online"
    elif ollama_state == "online" or neo4j_state == "online":
        dcx2_status = "degraded"
    else:
        dcx2_status = "offline"
    
    return dcx0_status, dcx1_status, dcx2_status


def _calculate_dcx_load(status: str) -> int:
    """Calculate load value based on DCX status."""
    load_map = {"online": 60, "degraded": 20, "offline": 0}
    return load_map.get(status, 0)


# === Root status endpoint ===
@app.get("/api/v1/status")
async def system_status():
    from datetime import datetime
    
    neo4j_state = _check_neo4j_connectivity()
    ollama_state = await _check_ollama_connectivity()
    now = datetime.now().isoformat()
    
    dcx0_status, dcx1_status, dcx2_status = _calculate_dcx_status(ollama_state, neo4j_state)
    
    dcx0_load = 45 if dcx0_status == "online" else 0
    dcx1_load = 30 if dcx1_status == "online" else 0
    dcx2_load = _calculate_dcx_load(dcx2_status)
    
    return {
        "system": "MoStar Grid API",
        "status": "operational" if neo4j_state == "online" else "degraded",
        "ollama_model": OLLAMA_MODEL,
        "tts_language": TTS_LANG,
        "neo4j": neo4j_state,
        "ollama": ollama_state,
        "layers": {
            "dcx0": {
                "name": "Mind (DCX0)",
                "status": dcx0_status,
                "load": dcx0_load,
                "lastPing": now if dcx0_status != "offline" else None
            },
            "dcx1": {
                "name": "Soul (DCX1)",
                "status": dcx1_status,
                "load": dcx1_load,
                "lastPing": now if dcx1_status != "offline" else None
            },
            "dcx2": {
                "name": "Body (DCX2)",
                "status": dcx2_status,
                "load": dcx2_load,
                "lastPing": now if dcx2_status != "offline" else None
            }
        }
    }


def _extract_prompt(content_type: str, body: dict | None, form_data: dict | None) -> str | None:
    if form_data:
        return form_data.get("prompt") or form_data.get("message")
    if body:
        return body.get("prompt") or body.get("message")
    return None


@app.post("/api/v1/reason")
async def reason_endpoint(request: Request):
    """
    Passes a prompt through the hybrid router and returns the generated reasoning.
    """
    try:
        prompt: str | None = None
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            body = await request.json()
            prompt = _extract_prompt(content_type, body, None)
        else:
            form = await request.form()
            prompt = _extract_prompt(content_type, None, dict(form))

        if not prompt:
            return JSONResponse(content={"error": "Missing prompt."}, status_code=400)

        neo4j_context = await fetch_neo4j_context(prompt)
        result = await route_query(prompt, SYSTEM_PROMPT, neo4j_context)
        log_mostar_moment(
            "Mind Layer",
            result.get("model_used", "unknown"),
            prompt,
            "reason",
            result.get("complexity_score", 0.0),
        )
        return result

    except Exception as e:
        err = f"Reasoning failed: {e}"
        log_mostar_moment("System", "Reason", err, "error", 0.3)
        return JSONResponse(content={"error": err}, status_code=500)


# === Voice synthesis endpoint ===
@app.post("/api/v1/voice")
async def speak_text(text: str = Form(...)):
    """
    Converts given text to speech and returns path to the generated audio.
    """
    try:
        filename = f"voice_{abs(hash(text))}.mp3"
        output_path = audio_dir / filename
        tts = gTTS(text=text, lang=TTS_LANG)
        tts.save(output_path)

        qid = log_mostar_moment("VoiceLayer", "User", f"Generated speech for: {text[:60]}...", "voice", 0.95)
        return {"audio_path": str(output_path), "quantum_id": qid}

    except Exception as e:
        fallback = audio_dir / "remostar_voice.mp3"
        if fallback.exists():
            qid = log_mostar_moment("VoiceLayer", "System", "Played fallback voice clip.", "voice", 0.70)
            return FileResponse(fallback, media_type="audio/mpeg", filename="remostar_voice.mp3")
        log_mostar_moment("System", "Voice", f"TTS failed: {e}", "error", 0.2)
        return JSONResponse(content={"error": str(e)}, status_code=500)


# === Moment logging endpoint ===
@app.post("/api/v1/moment")
async def moment_log(request: Request):
    body = await request.json()
    initiator = body.get("initiator", "unknown")
    receiver = body.get("receiver", "unknown")
    desc = body.get("description", "unspecified event")
    trig = body.get("trigger_type", "manual")
    res = float(body.get("resonance_score", 1.0))
    qid = log_mostar_moment(initiator, receiver, desc, trig, res)
    return {"quantum_id": qid, "status": "recorded"}


# === Root ping ===
@app.get("/")
async def root():
    return {"message": "🧩 MoStar Grid API online — unified reason, voice & memory."}
