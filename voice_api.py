"""
============================================================================
MOSTAR VOICE SERVICE — Sovereign TTS
============================================================================
Port: 41071
Engine: Piper (MIT, CPU, local, no cloud)
Voice: mostar-sovereign-v1

This is the REAL MoStar voice. Not Google. Not Microsoft. Not the browser.
A voice MoStar owns, running on infrastructure MoStar controls.

Seal: 🜃∴🜂
============================================================================
"""

import io
import os
import subprocess
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# ─────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────

VOICE_ROOT = Path.home() / "MoStar" / "voice"
PIPER_BIN = Path(os.getenv("PIPER_BIN", str(VOICE_ROOT / "piper" / "piper")))
VOICE_MODEL = Path(os.getenv("VOICE_MODEL", str(VOICE_ROOT / "models" / "en_US-libritts-high.onnx")))

VOICE_NAME = "mostar-sovereign-v1"

MOODS = {
    "stable":      {"length_scale": "1.0",  "sentence_silence": "0.4"},
    "ceremonial":  {"length_scale": "1.15", "sentence_silence": "0.6"},
    "alert":       {"length_scale": "0.9",  "sentence_silence": "0.2"},
    "reflective":  {"length_scale": "1.25", "sentence_silence": "0.7"},
}

# ─────────────────────────────────────────────────────────────────────────
# APP
# ─────────────────────────────────────────────────────────────────────────

app = FastAPI(title="MoStar Voice Service", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SpeakRequest(BaseModel):
    text: str
    mood: str = "ceremonial"


# ─────────────────────────────────────────────────────────────────────────
# TEXT SANITIZATION
# ─────────────────────────────────────────────────────────────────────────

GLYPH_STRIP = ["🜂", "🜄", "🜁", "🜃", "∴"]

def sanitize(text: str) -> str:
    cleaned = text
    for g in GLYPH_STRIP:
        cleaned = cleaned.replace(g, "")
    return " ".join(cleaned.split()).strip()


# ─────────────────────────────────────────────────────────────────────────
# HEALTH
# ─────────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    piper_ok = PIPER_BIN.exists()
    model_ok = VOICE_MODEL.exists()
    return {
        "status": "healthy" if (piper_ok and model_ok) else "degraded",
        "engine": "piper",
        "voice": VOICE_NAME,
        "piper_binary": piper_ok,
        "voice_model": model_ok,
        "seal": "🜃∴🜂",
    }


# ─────────────────────────────────────────────────────────────────────────
# SPEAK
# ─────────────────────────────────────────────────────────────────────────

@app.post("/speak")
async def speak(req: SpeakRequest):
    text = sanitize(req.text)
    if not text:
        raise HTTPException(status_code=400, detail="Empty text after sanitization")

    if not PIPER_BIN.exists():
        raise HTTPException(status_code=503, detail=f"Piper binary not found at {PIPER_BIN}")
    if not VOICE_MODEL.exists():
        raise HTTPException(status_code=503, detail=f"Voice model not found at {VOICE_MODEL}")

    mood_params = MOODS.get(req.mood, MOODS["ceremonial"])

    cmd = [
        str(PIPER_BIN),
        "--model", str(VOICE_MODEL),
        "--length_scale", mood_params["length_scale"],
        "--sentence_silence", mood_params["sentence_silence"],
        "--output_file", "-",
    ]

    try:
        result = subprocess.run(
            cmd,
            input=text.encode("utf-8"),
            capture_output=True,
            timeout=30,
        )
        if result.returncode != 0:
            err = result.stderr.decode("utf-8", errors="ignore")
            raise HTTPException(status_code=500, detail=f"Piper failed: {err[:200]}")
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Piper timed out")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Piper error: {str(e)[:200]}")

    return StreamingResponse(io.BytesIO(result.stdout), media_type="audio/wav")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "41071")))
