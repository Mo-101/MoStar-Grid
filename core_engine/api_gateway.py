#!/usr/bin/env python3
"""
🧠 MoStar Grid API Gateway
--------------------------
The purified Mind-Body interface. Ensures all external LLM intent and telemetry requests 
flow cleanly through the MoScript engine and align with the Canonical Telemetry v3 schema.
"""

import sys, os
from pathlib import Path
from fastapi import FastAPI, Request, Form, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv

# Ensure we can import from backend properly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core_engine.mostar_moments_log import log_mostar_moment
from core_engine.moscript_engine import MoScriptEngine
from core_engine.grid_telemetry import CanonicalTelemetryEngine
from truth_engine.truth_engine_service import TruthEngine
from gtts import gTTS

load_dotenv()

app = FastAPI(title="MoStar Grid Unified Gateway", version="3.0.0")

TTS_LANG = os.getenv("TTS_LANG", "en")
audio_dir = Path("data/voice_cache")
audio_dir.mkdir(parents=True, exist_ok=True)

# Shared MoScript engine strictly for Gateway translation actions
mo_engine = MoScriptEngine()
telemetry_engine = CanonicalTelemetryEngine(engine=mo_engine)
truth_engine = TruthEngine(engine=mo_engine)


@app.get("/api/v1/status")
async def system_status():
    """Fast check for the Executor + DB link."""
    return {
        "system": "MoStar Grid Gateway v3",
        "covenant": "active",
        "seal": mo_engine.bless("gateway_status")
    }


@app.get("/api/v1/telemetry")
async def get_telemetry():
    """Returns the Canonical Telemetry v3 structured strictly via MoScript traverses."""
    try:
        data = await telemetry_engine.get_grid_telemetry()
        return data
    except Exception as e:
        log_mostar_moment("System", "Gateway", f"Telemetry failed: {e}", "error", 0.0, layer="BODY")
        return JSONResponse(status_code=500, content={"error": str(e), "ok": False})


class ReasonRequest(BaseModel):
    prompt: str


@app.post("/api/v1/reason")
async def reason_endpoint(req: ReasonRequest, background_tasks: BackgroundTasks):
    """
    Standardizes all LLM interactions through the MoScript-governed TruthEngine,
    ensuring Ubuntu coherence and verifiable provenance.
    """
    try:
        if not req.prompt:
            return JSONResponse(content={"error": "Missing prompt."}, status_code=400)

        # Offload the pure reasoning path to the TruthEngine framework.
        # This replaces legacy 'orchestrator.py' fallback routes.
        result = await truth_engine.run(req.prompt)
        
        status = result.get("status")
        if status == "aligned":
            response_text = result.get("reasoning", "No valid reasoning synthesized")
            score = float(result.get("truth_score", 0.0))
        else:
            response_text = "TruthEngine declined to align response."
            score = 0.0

        return {
            "prompt": req.prompt,
            "response": response_text,
            "truth_score": score,
            "ubuntu_coherence": float(result.get("ubuntu_coherence", 0.0)),
            "seal": result.get("seal", "unsealed")
        }

    except Exception as e:
        err = f"Reasoning failed at gateway: {e}"
        log_mostar_moment("Gateway", "TruthEngine", err, "error", 0.0, layer="MIND")
        return JSONResponse(content={"error": err}, status_code=500)


@app.post("/api/v1/voice")
async def speak_text(text: str = Form(...)):
    """
    Sealed TTS creation. Must be tracked as a system event.
    """
    try:
        filename = f"voice_{abs(hash(text))}.mp3"
        output_path = audio_dir / filename
        tts = gTTS(text=text, lang=TTS_LANG)
        tts.save(output_path)

        qid = log_mostar_moment("VoiceGateway", "User", f"Synthesized speech: {text[:60]}...", "voice", 1.0, layer="BODY")
        return {"audio_path": str(output_path), "quantum_id": qid}

    except Exception as e:
        log_mostar_moment("System", "Voice", f"TTS failed: {e}", "error", 0.0, layer="BODY")
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.post("/api/v1/moment")
async def moment_log(request: Request):
    """Fallback manual log injection if absolutely needed, bound to BODY layer."""
    body = await request.json()
    initiator = body.get("initiator", "unknown")
    receiver = body.get("receiver", "unknown")
    desc = body.get("description", "unspecified event")
    trig = body.get("trigger_type", "manual")
    res = float(body.get("resonance_score", 1.0))
    layer = body.get("layer", "BODY")
    
    qid = log_mostar_moment(initiator, receiver, desc, trig, res, layer=layer)
    return {"quantum_id": qid, "status": "recorded", "seal": mo_engine.bless("manual_moment_log")}
