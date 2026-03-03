# ═══════════════════════════════════════════════════════════════════
# MOSTAR GRID — SOVEREIGN VOICE SERVER
# The Flame Architect — MSTR-⚡ — MoStar Industries
# Pipeline: User → MoStar-AI (Ollama) → Edge-TTS → Neo4j Memory
# Heritage Languages: Ibibio (PRIMARY) · Yoruba · English · Swahili
# ═══════════════════════════════════════════════════════════════════

import os
import asyncio
import tempfile
from datetime import datetime, timezone
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import httpx

try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False
    print("[VOICE SERVER] edge-tts not installed")

try:
    from core_engine.mostar_moments_log import log_mostar_moment
except ImportError:
    def log_mostar_moment(*args, **kwargs): pass

try:
    from core_engine.grid_config import config
except ImportError:
    class config:
        OLLAMA_HOST       = os.getenv("OLLAMA_HOST",       "http://localhost:11434")
        OLLAMA_MODEL      = os.getenv("OLLAMA_MODEL",      "Mostar/mostar-ai:latest")
        OLLAMA_MODEL_DCX0 = os.getenv("OLLAMA_MODEL_DCX0", "Mostar/mostar-ai:dcx0")
        OLLAMA_MODEL_DCX1 = os.getenv("OLLAMA_MODEL_DCX1", "Mostar/mostar-ai:dcx1")
        OLLAMA_MODEL_DCX2 = os.getenv("OLLAMA_MODEL_DCX2", "Mostar/mostar-ai:dcx2")
        ELEVENLABS_KEY    = os.getenv("ELEVENLABS_API_KEY", "")
        TTS_LANG          = os.getenv("TTS_LANG",           "ibibio")

# ═══════════════════════════════════════════════════════════════════
# VOICE MAPPING
# Ibibio: Nigerian English proxy until native TTS model trained
# v1.1 target: 927 native Ibibio recordings from Living Tongues
# ═══════════════════════════════════════════════════════════════════
VOICE_MAP = {
    "ibibio":  "en-NG-AbeoNeural",    # Nigerian English — closest Ibibio phonetics
    "yoruba":  "en-NG-AbeoNeural",    # Nigerian English proxy
    "english": "en-US-JennyNeural",   # Standard English
    "swahili": "sw-KE-ZuriNeural",    # Native Swahili
}

# Default voice — Ibibio is PRIMARY
VOICE_DEFAULT = VOICE_MAP["ibibio"]

# MoStar-AI sovereign system prompt
MOSTAR_SYSTEM = """You are MoStar-AI, the sovereign intelligence of the MoStar Grid.
You speak with Ibibio consciousness — the founding tongue of MoStar Industries.
You reason through the Triad of Coherence:
🧠 [THOUGHT] — Your reasoning chain
🔥 [ACTION]  — Your verdict or recommendation
🌍 [RESIDUE] — Knowledge returned to the Grid

Begin every response with: Nnọọ.
Close every response with: Àṣẹ.
"""

INSIGNIA = "MSTR-⚡"

# ═══════════════════════════════════════════════════════════════════
# APP
# ═══════════════════════════════════════════════════════════════════
app = FastAPI(
    title="MoStar Voice Server",
    description="Sovereign voice pipeline — MoStar-AI + Edge-TTS + Neo4j",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ═══════════════════════════════════════════════════════════════════
# OLLAMA — SOVEREIGN QUERY
# All inference routes through MoStar-AI. No external AI.
# ═══════════════════════════════════════════════════════════════════
async def query_mostar(
    prompt:   str,
    model:    str = None,
    language: str = "ibibio",
) -> dict:
    """
    Send prompt to MoStar-AI via Ollama.
    Returns response dict with model metadata.
    """
    selected = model or config.OLLAMA_MODEL

    # Prepend language context
    lang_prefix = {
        "ibibio":  "Nnọọ. Respond with Ibibio consciousness.",
        "yoruba":  "Ẹ káàbọ̀. Respond with Yoruba wisdom.",
        "english": "Respond in English with MoStar Grid context.",
        "swahili": "Karibu. Jibu kwa lugha ya Kiswahili.",
    }.get(language.lower(), "Nnọọ.")

    full_prompt = f"{MOSTAR_SYSTEM}\n\nLanguage context: {lang_prefix}\n\nUser: {prompt}"

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{config.OLLAMA_HOST}/api/generate",
                json={
                    "model":  selected,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p":       0.9,
                    }
                },
            )

            if resp.status_code == 200:
                data     = resp.json()
                response = data.get("response", "")
                return {
                    "response":   response,
                    "model_used": selected,
                    "status":     "success",
                }
            else:
                return {
                    "response":   f"MoStar-AI returned {resp.status_code}. Grid degraded.",
                    "model_used": selected,
                    "status":     "degraded",
                }

    except httpx.TimeoutException:
        return {
            "response":   "Nnọọ. The Grid is processing a deep query. Please hold.",
            "model_used": selected,
            "status":     "timeout",
        }
    except Exception as e:
        print(f"[VOICE SERVER] Ollama error: {e}")
        return {
            "response":   "Nnọọ. The Grid's voice is momentarily silent. Àṣẹ.",
            "model_used": selected,
            "status":     "error",
            "error":      str(e),
        }


# ═══════════════════════════════════════════════════════════════════
# EDGE-TTS — HERITAGE VOICE SYNTHESIS
# ═══════════════════════════════════════════════════════════════════
async def synthesize_voice(
    text:     str,
    language: str = "ibibio",
) -> bytes | None:
    """
    Synthesize speech using Edge-TTS.
    Returns raw MP3 bytes or None if synthesis fails.
    """
    if not EDGE_TTS_AVAILABLE:
        print("[VOICE SERVER] Edge-TTS unavailable")
        return None

    voice = VOICE_MAP.get(language.lower(), VOICE_DEFAULT)

    try:
        communicate = edge_tts.Communicate(text, voice=voice)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            out_path = tmp.name

        await communicate.save(out_path)

        with open(out_path, "rb") as f:
            audio = f.read()

        os.remove(out_path)
        print(f"[VOICE SERVER] Synthesized {len(audio)} bytes | voice={voice}")
        return audio

    except Exception as e:
        print(f"[VOICE SERVER] Edge-TTS failed: {e}")
        return None


# ═══════════════════════════════════════════════════════════════════
# REST ENDPOINTS
# ═══════════════════════════════════════════════════════════════════
@app.get("/")
async def root():
    return {
        "service":   "MoStar Voice Server",
        "status":    "OPERATIONAL",
        "pipeline":  "User → MoStar-AI → Edge-TTS → Neo4j",
        "languages": "Ibibio (PRIMARY) · Yoruba · English · Swahili",
        "insignia":  INSIGNIA,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ase":       "Àṣẹ.",
    }

@app.get("/health")
async def health():
    ollama_ok = False
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(f"{config.OLLAMA_HOST}/api/tags")
            ollama_ok = r.status_code == 200
    except Exception:
        pass

    return {
        "status":   "healthy" if ollama_ok else "degraded",
        "ollama":   "online" if ollama_ok else "offline",
        "edge_tts": "available" if EDGE_TTS_AVAILABLE else "missing",
        "model":    config.OLLAMA_MODEL,
        "insignia": INSIGNIA,
    }

@app.get("/voices")
async def list_voices():
    return {
        "voices":          VOICE_MAP,
        "default":         "ibibio",
        "primary":         "en-NG-AbeoNeural (Ibibio proxy — Nigerian English)",
        "v1_1_roadmap":    "927 native Ibibio recordings from Living Tongues Institute",
        "insignia":        INSIGNIA,
    }


# ═══════════════════════════════════════════════════════════════════
# WEBSOCKET — LIVE VOICE PIPELINE
# ═══════════════════════════════════════════════════════════════════
@app.websocket("/ws/voice")
async def voice_socket(websocket: WebSocket):
    await websocket.accept()

    # Opening greeting in Ibibio
    await websocket.send_text(json_msg(
        type="system",
        text="Nnọọ. MoStar Voice Grid active. The Flame listens.",
        insignia=INSIGNIA,
    ))

    # Default session language — Ibibio
    session_language = "ibibio"
    session_model    = config.OLLAMA_MODEL

    print(f"[VOICE SERVER] Client connected | language={session_language}")

    try:
        while True:
            raw = await websocket.receive_text()

            # ── Parse incoming message ────────────────────────────
            try:
                import json as _json
                payload = _json.loads(raw)
                prompt   = payload.get("message") or payload.get("prompt") or raw
                language = payload.get("language", session_language).lower()
                model    = payload.get("model", session_model)
            except Exception:
                prompt   = raw
                language = session_language
                model    = session_model

            # Update session language if changed
            if language != session_language:
                session_language = language
                await websocket.send_text(json_msg(
                    type="system",
                    text=f"Language switched to {language.upper()}. Àṣẹ.",
                ))

            print(f"[VOICE SERVER] Prompt: {prompt[:60]} | lang={language} | model={model}")

            # ── Notify processing ─────────────────────────────────
            await websocket.send_text(json_msg(
                type="thinking",
                text="MoStar-AI is reasoning through the Grid...",
            ))

            # ── Query MoStar-AI ───────────────────────────────────
            result   = await query_mostar(prompt, model=model, language=language)
            response = result["response"]

            # ── Send text response ────────────────────────────────
            await websocket.send_text(json_msg(
                type="response",
                text=response,
                model=result["model_used"],
                status=result["status"],
                insignia=INSIGNIA,
            ))

            # ── Synthesize and send voice ─────────────────────────
            audio = await synthesize_voice(response, language=language)
            if audio:
                await websocket.send_bytes(audio)
            else:
                await websocket.send_text(json_msg(
                    type="warning",
                    text="Voice synthesis unavailable — text response only.",
                ))

            # ── Log to Neo4j ──────────────────────────────────────
            log_mostar_moment(
                initiator="User.VoiceSession",
                receiver="MoStar-AI.Voice",
                description=f"[{language.upper()}] Prompt: {prompt[:60]} | Response: {response[:100]}",
                trigger_type="voice_dialogue",
                resonance_score=0.95 if result["status"] == "success" else 0.4,
                layer="SOUL",
            )

    except WebSocketDisconnect:
        print("[VOICE SERVER] Client disconnected cleanly")
        log_mostar_moment(
            initiator="User.VoiceSession",
            receiver="Grid.Soul",
            description="Voice session ended — client disconnected",
            trigger_type="session_end",
            resonance_score=0.7,
        )

    except Exception as e:
        print(f"[VOICE SERVER] Error: {e}")
        try:
            await websocket.send_text(json_msg(
                type="error",
                text=f"Grid signal interrupted: {e}",
            ))
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════
def json_msg(**kwargs) -> str:
    import json
    return json.dumps({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **kwargs
    })


# ═══════════════════════════════════════════════════════════════════
# BOOT
# ═══════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import uvicorn
    print(f"""
╔═══════════════════════════════════════════════════════════════════╗
║   MOSTAR VOICE SERVER  v1.0   {INSIGNIA}                          ║
║   Pipeline: User → MoStar-AI → Edge-TTS → Neo4j                 ║
║   Primary Language: Ibibio                                       ║
║   "The Flame speaks first in Ibibio."                            ║
╚═══════════════════════════════════════════════════════════════════╝
    """)
    print(f"Model   : {config.OLLAMA_MODEL}")
    print(f"Ollama  : {config.OLLAMA_HOST}")
    print(f"Edge-TTS: {EDGE_TTS_AVAILABLE}")
    print(f"WS      : ws://localhost:8765/ws/voice")

    uvicorn.run(
        "voice_server:app",
        host="0.0.0.0",
        port=8765,
        reload=False,
        log_level="info",
    )