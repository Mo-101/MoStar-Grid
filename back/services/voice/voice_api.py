"""
MoStar Voice API - Sovereign TTS runtime.

Port: 41071
Engine: Piper TTS
Voice: mostar-sovereign-v1
Seal: earth therefore fire
"""

import hashlib
import os
import subprocess
import time
from pathlib import Path
from typing import Optional

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool


VOICE_ROOT = Path(os.getenv("VOICE_ROOT", str(Path.home() / "MoStar" / "voice")))
PIPER_BIN = Path(os.getenv("PIPER_BIN", str(VOICE_ROOT / "piper" / "piper")))
VOICE_MODEL = Path(
    os.getenv("VOICE_MODEL", str(VOICE_ROOT / "models" / "en_GB-cori-high.onnx"))
)
AUDIO_OUT = Path(os.getenv("AUDIO_OUT", str(VOICE_ROOT / "audio")))
AUDIO_OUT.mkdir(parents=True, exist_ok=True)

GRID_API_URL = os.getenv("GRID_API_URL", "https://mostar-grid-api.onrender.com")
GRID_API_TOKEN = os.getenv("MOSTAR_SESSION_TOKEN", "")

VOICE_NAME = os.getenv("VOICE_NAME", "mostar-sovereign-v1")
MAX_AUDIO_FILES = int(os.getenv("MAX_AUDIO_FILES", "200"))
SEAL = "earth therefore fire"

GLYPH_SPOKEN = {
    "🜂": "fire",
    "🜄": "water",
    "🜁": "air",
    "🜃": "earth",
    "∴": "therefore",
    "∞": "infinity",
    "🔥": "flame",
    "⚔️": "blade",
    "🛡️": "shield",
    "🧠": "deep mind",
    "❤️": "heart",
    "⚖️": "balance",
    "👑": "crown",
    "✍️": "scribe",
    "⚙️": "gear",
}

CODEX_PREFIXES = {
    "woo_tak": "By the flame of Woo Tak, architect of the grid:",
    "alpha_mostar": "Alpha Mostar speaks:",
    "deepcal": "From the depths of DeepCAL:",
    "molink": "Through the heart of Molink:",
    "sigma": "In perfect balance, Sigma declares:",
    "flameborn": "The Flameborn whispers:",
}

CODEX_SUFFIXES = {
    "ceremonial": "Thus it is sealed.",
    "prophecy": "So the flame has spoken.",
    "reflective": "Let this be remembered.",
    "stable": "Transmission complete.",
    "alert": "Immediate attention is required.",
    "whisper": "The whisper has been carried.",
}

MOODS = {
    "stable": {"length_scale": "1.0", "sentence_silence": "0.4"},
    "ceremonial": {"length_scale": "1.15", "sentence_silence": "0.6"},
    "alert": {"length_scale": "0.9", "sentence_silence": "0.2"},
    "reflective": {"length_scale": "1.25", "sentence_silence": "0.7"},
    "prophecy": {"length_scale": "1.3", "sentence_silence": "0.8"},
    "whisper": {"length_scale": "1.5", "sentence_silence": "1.0"},
}


app = FastAPI(
    title="MoStar Voice API",
    version="1.0.0",
    description="Sovereign TTS runtime for MoStar Industries and all its Artifacts.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/audio", StaticFiles(directory=str(AUDIO_OUT)), name="audio")


class SpeakRequest(BaseModel):
    text: str = Field(default="", description="Text to speak.")
    mood: str = Field(
        default="ceremonial",
        description="stable, ceremonial, alert, reflective, prophecy, whisper",
    )
    speaker: Optional[str] = Field(default=None, description="Codex speaker key.")
    persona: Optional[str] = Field(
        default=None,
        description="Legacy frontend alias for speaker.",
    )
    moment_id: Optional[str] = Field(
        default=None,
        description="Optional MoStarMoment ID from Grid.",
    )
    codex: bool = Field(
        default=True,
        description="Apply Codex prefix/suffix and glyph speech.",
    )
    return_file: bool = Field(
        default=False,
        description="Return WAV file directly instead of JSON.",
    )


class SpeakResponse(BaseModel):
    ok: bool
    audio_url: str
    engine: str
    voice: str
    cached: bool
    mood: str
    speaker: Optional[str]
    persona: str
    text_spoken: str
    seal: str
    duration_ms: int
    request_id: str


class SpeakVerifyResponse(BaseModel):
    ok: bool
    ready: bool
    engine: str
    voice: str
    piper_binary: bool
    voice_model: bool
    audio_file: Optional[str]
    file_sha256: Optional[str]
    duration_ms: int
    seal: str
    detail: str


def replace_glyphs_with_speech(text: str) -> str:
    result = text
    for glyph, spoken in GLYPH_SPOKEN.items():
        result = result.replace(glyph, f" {spoken} ")
    return " ".join(result.split())


def enrich_with_codex(text: str, speaker: Optional[str], mood: str) -> str:
    enriched = text.strip()

    if speaker and speaker in CODEX_PREFIXES:
        enriched = f"{CODEX_PREFIXES[speaker]} {enriched}"

    suffix = CODEX_SUFFIXES.get(mood)
    if suffix:
        enriched = f"{enriched}. {suffix}"

    return enriched


def breath_process(text: str) -> str:
    return text.replace(".", " ... ").replace("!", " ... ").replace("?", " ... ")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


async def fetch_moment_text(moment_id: str) -> str:
    headers = {}
    if GRID_API_TOKEN:
        headers["Authorization"] = f"Bearer {GRID_API_TOKEN}"

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(
                f"{GRID_API_URL}/api/moments/{moment_id}",
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()
            return (
                data.get("spoken")
                or data.get("think_output")
                or data.get("content")
                or ""
            )
        except Exception as exc:
            raise HTTPException(
                status_code=502,
                detail=f"Failed to fetch Grid moment: {str(exc)[:200]}",
            ) from exc


def assert_piper_ready() -> None:
    if not PIPER_BIN.exists():
        raise HTTPException(
            status_code=503,
            detail=f"Piper binary not found: {PIPER_BIN}",
        )
    if not VOICE_MODEL.exists():
        raise HTTPException(
            status_code=503,
            detail=f"Voice model not found: {VOICE_MODEL}",
        )


def synthesize(text: str, mood: str, out_file: Path) -> None:
    assert_piper_ready()

    params = MOODS.get(mood, MOODS["ceremonial"])
    processed_text = breath_process(text)

    cmd = [
        str(PIPER_BIN),
        "--model",
        str(VOICE_MODEL),
        "--length_scale",
        params["length_scale"],
        "--sentence_silence",
        params["sentence_silence"],
        "--output_file",
        str(out_file),
    ]

    try:
        result = subprocess.run(
            cmd,
            input=processed_text.encode("utf-8"),
            capture_output=True,
            timeout=45,
            check=False,
        )

        if result.returncode != 0:
            err = result.stderr.decode("utf-8", errors="ignore")
            raise HTTPException(status_code=500, detail=f"Piper failed: {err[:300]}")

    except subprocess.TimeoutExpired as exc:
        raise HTTPException(status_code=504, detail="Piper synthesis timed out") from exc


@app.get("/")
async def root():
    return {
        "name": "MoStar Voice API",
        "engine": "piper",
        "voice": VOICE_NAME,
        "seal": SEAL,
        "routes": ["/health", "/speak", "/speak/verify", "/voices", "/moods", "/cleanup"],
    }


@app.get("/health")
async def health():
    grid_reachable = False

    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get(f"{GRID_API_URL}/api/health")
            grid_reachable = resp.status_code == 200
    except Exception:
        pass

    piper_ok = PIPER_BIN.exists()
    model_ok = VOICE_MODEL.exists()

    return {
        "status": "healthy" if piper_ok and model_ok else "degraded",
        "engine": "piper",
        "voice": VOICE_NAME,
        "piper_binary": piper_ok,
        "voice_model": model_ok,
        "grid_reachable": grid_reachable,
        "audio_dir": str(AUDIO_OUT),
        "seal": SEAL,
    }


@app.get("/voices")
async def voices():
    return {
        "default": VOICE_NAME,
        "voices": [
            {
                "id": VOICE_NAME,
                "engine": "piper",
                "model": str(VOICE_MODEL),
                "status": "available" if VOICE_MODEL.exists() else "missing",
            }
        ],
    }


@app.get("/moods")
async def moods():
    return {
        "moods": MOODS,
        "speakers": list(CODEX_PREFIXES.keys()),
        "glyphs": GLYPH_SPOKEN,
    }


@app.post("/speak", response_model=None)
async def speak(req: SpeakRequest):
    text_to_speak = req.text
    speaker = req.speaker or req.persona

    if req.moment_id:
        text_to_speak = await fetch_moment_text(req.moment_id)

    if not text_to_speak or not text_to_speak.strip():
        raise HTTPException(status_code=400, detail="Empty text to speak")

    if req.mood not in MOODS:
        raise HTTPException(status_code=400, detail=f"Invalid mood: {req.mood}")

    if req.codex:
        text_to_speak = replace_glyphs_with_speech(text_to_speak)
        text_to_speak = enrich_with_codex(text_to_speak, speaker, req.mood)

    cache_str = f"{text_to_speak}|{req.mood}|{speaker or ''}|{req.moment_id or ''}"
    digest = hashlib.sha256(cache_str.encode("utf-8")).hexdigest()[:16]
    out_file = AUDIO_OUT / f"woo-{digest}.wav"

    cached = out_file.exists()
    started = time.monotonic()

    if not cached:
        await run_in_threadpool(synthesize, text_to_speak, req.mood, out_file)

    duration_ms = int((time.monotonic() - started) * 1000)

    if req.return_file:
        return FileResponse(
            path=str(out_file),
            media_type="audio/wav",
            filename=out_file.name,
        )

    response = SpeakResponse(
        ok=True,
        audio_url=f"/audio/{out_file.name}",
        engine="piper",
        voice=VOICE_NAME,
        cached=cached,
        mood=req.mood,
        speaker=speaker,
        persona=speaker or VOICE_NAME,
        text_spoken=text_to_speak,
        seal=SEAL,
        duration_ms=duration_ms,
        request_id=digest,
    )
    return response.model_dump()


@app.api_route("/speak/verify", methods=["GET", "POST"], response_model=None)
async def speak_verify():
    started = time.monotonic()
    piper_ok = PIPER_BIN.exists()
    model_ok = VOICE_MODEL.exists()
    out_file: Optional[Path] = None

    if not piper_ok or not model_ok:
        response = SpeakVerifyResponse(
            ok=False,
            ready=False,
            engine="piper",
            voice=VOICE_NAME,
            piper_binary=piper_ok,
            voice_model=model_ok,
            audio_file=None,
            file_sha256=None,
            duration_ms=int((time.monotonic() - started) * 1000),
            seal=SEAL,
            detail="Piper binary or voice model missing",
        )
        return JSONResponse(status_code=503, content=response.model_dump())

    digest = hashlib.sha256(f"verify|{time.time_ns()}".encode("utf-8")).hexdigest()[:16]
    out_file = AUDIO_OUT / f"verify-{digest}.wav"

    try:
        await run_in_threadpool(synthesize, "Runtime ready.", "stable", out_file)
        audio_hash = await run_in_threadpool(file_sha256, out_file)
        ready = out_file.exists() and out_file.stat().st_size > 0
        response = SpeakVerifyResponse(
            ok=ready,
            ready=ready,
            engine="piper",
            voice=VOICE_NAME,
            piper_binary=True,
            voice_model=True,
            audio_file=out_file.name,
            file_sha256=audio_hash,
            duration_ms=int((time.monotonic() - started) * 1000),
            seal=SEAL,
            detail="Runtime synthesis verified" if ready else "Synthesis produced no audio",
        )
        return JSONResponse(
            status_code=200 if ready else 503,
            content=response.model_dump(),
        )
    except HTTPException as exc:
        response = SpeakVerifyResponse(
            ok=False,
            ready=False,
            engine="piper",
            voice=VOICE_NAME,
            piper_binary=piper_ok,
            voice_model=model_ok,
            audio_file=out_file.name if out_file else None,
            file_sha256=None,
            duration_ms=int((time.monotonic() - started) * 1000),
            seal=SEAL,
            detail=str(exc.detail),
        )
        return JSONResponse(status_code=exc.status_code, content=response.model_dump())
    finally:
        if out_file is not None:
            out_file.unlink(missing_ok=True)


@app.post("/cleanup")
async def cleanup():
    files = sorted(AUDIO_OUT.glob("woo-*.wav"), key=lambda path: path.stat().st_mtime)
    removed = 0

    while len(files) > MAX_AUDIO_FILES:
        oldest = files.pop(0)
        oldest.unlink(missing_ok=True)
        removed += 1

    return {
        "ok": True,
        "removed": removed,
        "remaining": len(files),
        "limit": MAX_AUDIO_FILES,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "voice_api:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "41071")),
        reload=False,
    )
