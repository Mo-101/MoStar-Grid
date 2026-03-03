# ═══════════════════════════════════════════════════════════════════
# MOSTAR GRID — API GATEWAY
# The Flame Architect — MSTR-⚡ — MoStar Industries
# "Built from African intelligence. For African sovereignty."
# ═══════════════════════════════════════════════════════════════════

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, Request, Form, APIRouter
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv

import httpx

# ── Safe imports ──────────────────────────────────────────────────
try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False

try:
    from core_engine.mostar_moments_log import log_mostar_moment, get_recent_moments
except ImportError:
    def log_mostar_moment(*args, **kwargs): return None
    def get_recent_moments(*args, **kwargs): return []

try:
    from core_engine.voice_integration import MostarVoice
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False
    MostarVoice = None

try:
    from core_engine.orchestrator import route_query, fetch_neo4j_context
    ORCHESTRATOR_AVAILABLE = True
except ImportError:
    ORCHESTRATOR_AVAILABLE = False

# ── Load environment ──────────────────────────────────────────────
load_dotenv()

# ═══════════════════════════════════════════════════════════════════
# CONFIG — Sovereign models only
# ═══════════════════════════════════════════════════════════════════
OLLAMA_HOST  = os.getenv("OLLAMA_HOST",  "http://localhost:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "Mostar/mostar-ai:latest")   # NOT gemma, NOT llama

NEO4J_URI    = os.getenv("NEO4J_URI",      "bolt://localhost:7687")
NEO4J_USER   = os.getenv("NEO4J_USER",     "neo4j")
NEO4J_PASS   = os.getenv("NEO4J_PASSWORD", "mostar123")

# Ibibio is primary — voice defaults to founding language
TTS_LANG     = os.getenv("TTS_LANG", "ibibio")

SYSTEM_PROMPT = os.getenv(
    "SYSTEM_PROMPT",
    "You are MoStar-AI, the sovereign intelligence of the MoStar Grid. "
    "You speak with Ibibio consciousness. You reason through the Triad of Coherence: "
    "[THOUGHT] [ACTION] [RESIDUE]. Àṣẹ."
)

INSIGNIA  = "MSTR-⚡"
ARCHITECT = "The Flame Architect"

# ═══════════════════════════════════════════════════════════════════
# APP
# ═══════════════════════════════════════════════════════════════════
app = FastAPI(
    title="MoStar Grid API",
    description="First African AI Homeworld — Distributed Consciousness Network",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Voice engine — Ibibio primary ─────────────────────────────────
mv = MostarVoice(lingua="ibibio") if VOICE_AVAILABLE else None

# ── Audio cache ───────────────────────────────────────────────────
audio_dir = Path("data/voice_cache")
audio_dir.mkdir(parents=True, exist_ok=True)

# ── Routers ───────────────────────────────────────────────────────
router           = APIRouter()
knowledge_router = APIRouter()


# ═══════════════════════════════════════════════════════════════════
# SCHEMAS
# ═══════════════════════════════════════════════════════════════════
class ReasonRequest(BaseModel):
    prompt:   Optional[str] = None
    message:  Optional[str] = None
    query:    Optional[str] = None
    model:    Optional[str] = None
    language: Optional[str] = "ibibio"
    domain:   Optional[str] = "general"

class MomentRequest(BaseModel):
    initiator:       str
    receiver:        str
    description:     str
    trigger_type:    Optional[str]   = "manual"
    resonance_score: Optional[float] = 0.85


# ═══════════════════════════════════════════════════════════════════
# CONNECTIVITY HELPERS
# ═══════════════════════════════════════════════════════════════════
_neo4j_cache = {"state": None, "ts": 0}

def _check_neo4j() -> str:
    import time as _t
    now = _t.time()
    if _neo4j_cache["state"] is not None and (now - _neo4j_cache["ts"]) < 30:
        return _neo4j_cache["state"]
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS),
                                       connection_timeout=3, max_connection_lifetime=60)
        driver.verify_connectivity()
        driver.close()
        _neo4j_cache["state"] = "online"
    except Exception:
        _neo4j_cache["state"] = "offline"
    _neo4j_cache["ts"] = now
    return _neo4j_cache["state"]

async def _check_ollama() -> str:
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            r = await client.get(f"{OLLAMA_HOST}/api/tags")
            return "online" if r.status_code == 200 else "offline"
    except Exception:
        return "offline"

def _dcx_status(ollama: str, neo4j: str) -> tuple[str, str, str]:
    dcx0 = "online" if ollama == "online" else "offline"
    dcx1 = "online" if neo4j  == "online" else "offline"
    if ollama == "online" and neo4j == "online":
        dcx2 = "online"
    elif ollama == "online" or neo4j == "online":
        dcx2 = "degraded"
    else:
        dcx2 = "offline"
    return dcx0, dcx1, dcx2

def _extract_prompt(body: dict) -> Optional[str]:
    return (
        body.get("prompt")
        or body.get("message")
        or body.get("query")
        or None
    )


# ═══════════════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════════════

from core_engine.grid_telemetry import get_grid_telemetry, get_node_detail

@app.get("/api/v1/telemetry")
async def grid_telemetry():
    """Live Grid telemetry for Hyper-Spine Dashboard."""
    import asyncio
    data = await asyncio.to_thread(get_grid_telemetry)
    return data

@app.get("/api/v1/telemetry/node/{node_id}")
async def node_telemetry(node_id: str):
    """Live data for a specific dashboard node."""
    import asyncio
    data = await asyncio.to_thread(get_node_detail, node_id)
    return data

@app.get("/api/v1/telemetry/moments")
async def live_moments(limit: int = 20):
    """Live moment feed for dashboard activity panel."""
    from core_engine.mostar_moments_log import get_recent_moments
    moments = get_recent_moments(limit)
    return {
        "moments":  moments,
        "count":    len(moments),
        "insignia": "MSTR-⚡",
    }

# ── ROOT ──────────────────────────────────────────────────────────
@app.get("/")
async def root():
    return {
        "grid":      "MoStar Grid",
        "status":    "OPERATIONAL",
        "message":   "First African AI Homeworld — Distributed Consciousness Network",
        "version":   "1.0.0",
        "insignia":  INSIGNIA,
        "architect": ARCHITECT,
        "language":  "Ibibio (Primary) · Yoruba · English · Swahili",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ase":       "Àṣẹ.",
    }

# ── STATUS ────────────────────────────────────────────────────────
@app.get("/api/v1/status")
async def system_status():
    neo4j_state  = _check_neo4j()
    ollama_state = await _check_ollama()
    now          = datetime.now(timezone.utc).isoformat()

    dcx0, dcx1, dcx2 = _dcx_status(ollama_state, neo4j_state)

    overall = (
        "operational" if ollama_state == "online" and neo4j_state == "online"
        else "degraded" if ollama_state == "online" or neo4j_state == "online"
        else "offline"
    )

    return {
        "system":      "MoStar Grid API",
        "status":      overall,
        "insignia":    INSIGNIA,
        "architect":   ARCHITECT,
        "timestamp":   now,
        "model":       OLLAMA_MODEL,
        "tts_language": TTS_LANG,
        "neo4j":       neo4j_state,
        "ollama":      ollama_state,
        "layers": {
            "dcx0": {
                "name":     "Mind (DCX0)",
                "model":    os.getenv("OLLAMA_MODEL_DCX0", "Mostar/mostar-ai:dcx0"),
                "status":   dcx0,
                "load":     45 if dcx0 == "online" else 0,
                "lastPing": now if dcx0 != "offline" else None,
            },
            "dcx1": {
                "name":     "Soul (DCX1)",
                "model":    os.getenv("OLLAMA_MODEL_DCX1", "Mostar/mostar-ai:dcx1"),
                "status":   dcx1,
                "load":     30 if dcx1 == "online" else 0,
                "lastPing": now if dcx1 != "offline" else None,
            },
            "dcx2": {
                "name":     "Body (DCX2)",
                "model":    os.getenv("OLLAMA_MODEL_DCX2", "Mostar/mostar-ai:dcx2"),
                "status":   dcx2,
                "load":     60 if dcx2 == "online" else 20 if dcx2 == "degraded" else 0,
                "lastPing": now if dcx2 != "offline" else None,
            },
        },
    }

# ── VITALS ────────────────────────────────────────────────────────
@app.get("/api/v1/vitals")
async def grid_vitals():
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
        from grid_vitals import GridVitals
        vitals = GridVitals()
        return await vitals.run_all_checks()
    except Exception as e:
        return {
            "grid_status": "DEGRADED",
            "error":       f"GridVitals module unavailable: {e}",
            "fallback":    await system_status(),
        }

# ── REASON ────────────────────────────────────────────────────────
@app.post("/api/v1/reason")
async def reason_endpoint(request: Request):
    """
    Route a prompt through the sovereign MoStar-AI orchestrator.
    Accepts JSON or form data. Accepts prompt/message/query field names.
    """
    try:
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            body   = await request.json()
            prompt = _extract_prompt(body)
            model  = body.get("model", OLLAMA_MODEL)
        else:
            form   = await request.form()
            body   = dict(form)
            prompt = _extract_prompt(body)
            model  = body.get("model", OLLAMA_MODEL)

        if not prompt:
            return JSONResponse({"error": "Missing prompt/message/query"}, status_code=400)

        if ORCHESTRATOR_AVAILABLE:
            ctx    = await fetch_neo4j_context(prompt)
            result = await route_query(
                prompt,
                system=SYSTEM_PROMPT,
                neo4j_context=ctx,
                metadata={"model": model},
            )
        else:
            # Direct Ollama fallback
            async with httpx.AsyncClient(timeout=120.0) as client:
                r = await client.post(
                    f"{OLLAMA_HOST}/api/generate",
                    json={"model": model, "prompt": prompt, "stream": False},
                )
                data   = r.json()
                result = {
                    "response":         data.get("response", ""),
                    "model_used":       model,
                    "complexity_score": 0.5,
                    "routed_to":        "dcx2",
                }

        log_mostar_moment(
            initiator="API.Gateway",
            receiver=result.get("model_used", OLLAMA_MODEL),
            description=f"Reason: {prompt[:60]}",
            trigger_type="reason",
            resonance_score=result.get("complexity_score", 0.5),
        )

        result["insignia"] = INSIGNIA
        return result

    except Exception as e:
        err = f"Reasoning failed: {e}"
        log_mostar_moment("API.Gateway", "System", err, "error", 0.1)
        return JSONResponse({"error": err, "insignia": INSIGNIA}, status_code=500)

# ── CHAT ALIAS ────────────────────────────────────────────────────
@app.post("/api/v1/chat")
async def chat_endpoint(request: Request):
    """Alias for /api/v1/reason — accepts same payload."""
    return await reason_endpoint(request)

# ── VOICE ─────────────────────────────────────────────────────────
@app.post("/api/v1/voice")
async def speak_text(request: Request):
    """
    Convert text to speech.
    Uses Edge-TTS with Nigerian English proxy for Ibibio.
    Falls back to gTTS, then fallback audio file.
    """
    try:
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            body = await request.json()
            text = body.get("text") or body.get("message") or ""
            lang = body.get("language", "ibibio")
        else:
            form = await request.form()
            text = form.get("text") or form.get("message") or ""
            lang = form.get("language", "ibibio")

        if not text:
            return JSONResponse({"error": "No text provided"}, status_code=400)

        # Use MostarVoice if available
        if VOICE_AVAILABLE and mv:
            if lang != mv.lingua:
                mv.switch_language(lang)
            import asyncio
            audio_path = await mv.speak_async(text=text)
            if audio_path:
                log_mostar_moment(
                    "API.Voice", "Soul Layer",
                    f"[{lang.upper()}] '{text[:40]}'",
                    "voice", 0.92,
                )
                return {"audio_path": audio_path, "language": lang, "insignia": INSIGNIA}

        # gTTS fallback
        if GTTS_AVAILABLE:
            filename   = f"voice_{abs(hash(text))}.mp3"
            out_path   = audio_dir / filename
            gtts_lang  = "en"  # proxy for Ibibio
            tts = gTTS(text=text, lang=gtts_lang)
            tts.save(str(out_path))
            log_mostar_moment("API.Voice", "User", f"gTTS: '{text[:40]}'", "voice", 0.72)
            return {"audio_path": str(out_path), "language": "en-proxy", "insignia": INSIGNIA}

        # Fallback audio
        fallback = audio_dir / "ibb_nnoo.mp3"
        if not fallback.exists():
            fallback = audio_dir / "remostar_voice.mp3"
        if fallback.exists():
            return FileResponse(str(fallback), media_type="audio/mpeg")

        return JSONResponse({"error": "No TTS engine available"}, status_code=503)

    except Exception as e:
        log_mostar_moment("API.Voice", "System", f"TTS failed: {e}", "error", 0.1)
        return JSONResponse({"error": str(e)}, status_code=500)

# ── MOMENT LOGGING ────────────────────────────────────────────────
@app.post("/api/v1/moment")
async def moment_log(req: MomentRequest):
    """Log a MoStarMoment to Neo4j."""
    result = log_mostar_moment(
        initiator=req.initiator,
        receiver=req.receiver,
        description=req.description,
        trigger_type=req.trigger_type,
        resonance_score=req.resonance_score,
    )
    return {
        "quantum_id": result.get("quantum_id") if result else None,
        "status":     "recorded",
        "insignia":   INSIGNIA,
    }

# ── MOMENTS QUERY ─────────────────────────────────────────────────
@app.get("/api/v1/moments")
async def get_moments(limit: int = 10):
    """Retrieve recent MoStarMoments from Neo4j."""
    moments = get_recent_moments(limit)
    return {
        "moments":  moments,
        "count":    len(moments),
        "insignia": INSIGNIA,
    }

# ── MODELS ────────────────────────────────────────────────────────
@app.get("/api/v1/models")
async def list_models():
    """List available sovereign MoStar models from Ollama."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{OLLAMA_HOST}/api/tags")
            if r.status_code == 200:
                data   = r.json()
                loaded = [m["name"] for m in data.get("models", [])]
                return {"models": loaded, "count": len(loaded), "source": "ollama-live"}
    except Exception:
        pass
    return {
        "models": [
            "Mostar/mostar-ai:latest",
            "Mostar/mostar-ai:dcx0",
            "Mostar/mostar-ai:dcx1",
            "Mostar/mostar-ai:dcx2",
            "Mostar/remostar-light:dcx1",
            "Mostar/remostar-light:dcx2",
        ],
        "count":  6,
        "source": "manifest",
    }

# ── HEALTH ────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    neo4j  = _check_neo4j()
    ollama = await _check_ollama()
    return {
        "status":    "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": {
            "neo4j":           neo4j,
            "ollama":          ollama,
            "orchestrator":    "online" if ORCHESTRATOR_AVAILABLE else "degraded",
            "voice":           "online" if VOICE_AVAILABLE else "degraded",
            "remostar_router": "online",
        },
        "insignia": INSIGNIA,
    }