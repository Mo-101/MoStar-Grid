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

import hashlib
import os
import subprocess
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# ─────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────

VOICE_ROOT = Path.home() / "MoStar" / "voice"
PIPER_BIN = VOICE_ROOT / "piper" / "piper"
VOICE_MODEL = VOICE_ROOT / "models" / "en_US-libritts-high.onnx"
AUDIO_OUT = VOICE_ROOT / "audio"
AUDIO_OUT.mkdir(parents=True, exist_ok=True)

VOICE_NAME = "mostar-sovereign-v1"

# Mood → Piper parameters (length_scale = pacing, sentence_silence = pauses)
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

# Serve generated audio files
app.mount("/audio", StaticFiles(directory=str(AUDIO_OUT)), name="audio")


class SpeakRequest(BaseModel):
    text: str
    mood: str = "ceremonial"


# ─────────────────────────────────────────────────────────────────────────
# TEXT SANITIZATION
# ─────────────────────────────────────────────────────────────────────────

GLYPH_STRIP = ["🜂", "🜄", "🜁", "🜃", "∴", "🜃∴🜂"]

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
# SPEAK — the core endpoint
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

    # Deterministic filename per (text, mood) — cache identical requests
    digest = hashlib.sha256(f"{text}|{req.mood}".encode()).hexdigest()[:16]
    out_file = AUDIO_OUT / f"woo-{digest}.wav"

    # Return cached audio if it exists
    if out_file.exists():
        return {
            "ok": True,
            "audio_url": f"/audio/{out_file.name}",
            "engine": "piper",
            "voice": VOICE_NAME,
            "cached": True,
        }

    # Generate via Piper
    try:
        cmd = [
            str(PIPER_BIN),
            "--model", str(VOICE_MODEL),
            "--length_scale", mood_params["length_scale"],
            "--sentence_silence", mood_params["sentence_silence"],
            "--output_file", str(out_file),
        ]
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

    return {
        "ok": True,
        "audio_url": f"/audio/{out_file.name}",
        "engine": "piper",
        "voice": VOICE_NAME,
        "cached": False,
    }


# ─────────────────────────────────────────────────────────────────────────
# CLEANUP — purge old audio (keep last 200 files)
# ─────────────────────────────────────────────────────────────────────────

@app.post("/cleanup")
async def cleanup():
    files = sorted(AUDIO_OUT.glob("woo-*.wav"), key=lambda p: p.stat().st_mtime)
    removed = 0
    while len(files) > 200:
        oldest = files.pop(0)
        oldest.unlink()
        removed += 1
    return {"ok": True, "removed": removed, "remaining": len(files)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=41071)
