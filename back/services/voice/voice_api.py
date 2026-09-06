"""
MoStar Voice API - Sovereign TTS runtime.

Port: 41071
Engine: Piper TTS
Voice: mostar-sovereign-v1
Seal: earth therefore fire
"""

import hashlib
import io
import json
import os
import subprocess
import tempfile
import time
import wave
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
AUDIO_OUT = Path(os.getenv("AUDIO_OUT", str(VOICE_ROOT / "audio")))
VOICE_MODEL_DIR = Path(os.getenv("VOICE_MODEL_DIR", str(VOICE_ROOT / "models")))
AUDIO_OUT.mkdir(parents=True, exist_ok=True)

GRID_API_URL = os.getenv("GRID_API_URL", "https://mostar-grid-api.onrender.com")
GRID_API_TOKEN = os.getenv("MOSTAR_SESSION_TOKEN", "")

MAX_AUDIO_FILES = int(os.getenv("MAX_AUDIO_FILES", "200"))
SYNTHESIS_TIMEOUT_SECONDS = int(os.getenv("SYNTHESIS_TIMEOUT_SECONDS", "180"))
SEAL = "earth therefore fire"

# Voice registry — maps a stable voice_id to an on-disk Piper model.
# Models live in VOICE_ROOT/models; add new entries here once a .onnx is
# downloaded there. Gender/character notes are best-effort (Piper voice
# names come from their training datasets, not a verified gender label).
VOICE_NAME = os.getenv("VOICE_NAME", "mostar-clear-v1")
VOICES: dict[str, dict[str, str]] = {
    "mostar-sovereign-v1": {
        "model": str(VOICE_MODEL_DIR / "en_GB-cori-high.onnx"),
        "label": "Cori (en-GB) — ceremonial",
    },
    "mostar-clear-v1": {
        "model": str(VOICE_MODEL_DIR / "en_US-lessac-high.onnx"),
        "label": "Lessac (en-US) — default, natural conversational pacing",
    },
    "mostar-libritts-v1": {
        "model": str(VOICE_MODEL_DIR / "en_US-libritts-high.onnx"),
        "label": "LibriTTS (en-US) — multi-speaker corpus",
    },
}
# Back-compat: VOICE_MODEL env var, if set, overrides the default entry's model.
if os.getenv("VOICE_MODEL"):
    VOICES[VOICE_NAME]["model"] = os.getenv("VOICE_MODEL")

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
    "conversational": {"length_scale": "1.0", "sentence_silence": "0.2"},
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
    description="Sovereign TTS runtime for MoStar Intelligent Systems and all its Artifacts.",
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
        default="conversational",
        description="stable, ceremonial, alert, reflective, prophecy, whisper",
    )
    voice: str = Field(
        default=VOICE_NAME,
        description="voice_id from GET /voices. Falls back to the default voice if unknown.",
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
        default=False,
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
    synthesis_ms: int
    request_id: str


class NarrateRequest(BaseModel):
    segments: list[str] = Field(min_length=1, max_length=16)
    mood: str = Field(default="conversational")
    voice: str = Field(default=VOICE_NAME)


class NarrationSegment(BaseModel):
    text: str
    start_ms: int
    end_ms: int


class NarrateResponse(BaseModel):
    ok: bool
    audio_url: str
    audio_ms: int
    synthesis_ms: int
    segments: list[NarrationSegment]
    engine: str
    voice: str
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


def resolve_voice(voice_id: Optional[str]) -> tuple[str, Path]:
    """Resolve a requested voice_id to a registered (id, model_path) pair.

    Falls back to the default voice — and logs it — if the id is unknown,
    rather than failing the whole request over a typo'd voice name.
    """
    candidate = voice_id or VOICE_NAME
    entry = VOICES.get(candidate)
    if entry is None:
        print(f"[voice_api] unknown voice_id={candidate!r}, falling back to {VOICE_NAME!r}")
        candidate = VOICE_NAME
        entry = VOICES[VOICE_NAME]

    model_path = Path(entry["model"])
    if not model_path.exists() and candidate != VOICE_NAME:
        print(
            f"[voice_api] missing model for voice_id={candidate!r}: {model_path}; "
            f"falling back to {VOICE_NAME!r}"
        )
        candidate = VOICE_NAME
        entry = VOICES[VOICE_NAME]
        model_path = Path(entry["model"])

    return candidate, model_path


def assert_piper_ready(voice_model: Path) -> None:
    if not PIPER_BIN.exists():
        raise HTTPException(
            status_code=503,
            detail=f"Piper binary not found: {PIPER_BIN}",
        )
    if not voice_model.exists():
        raise HTTPException(
            status_code=503,
            detail=f"Voice model not found: {voice_model}",
        )


def synthesize(text: str, mood: str, voice_model: Path, out_file: Path) -> None:
    assert_piper_ready(voice_model)

    params = MOODS.get(mood, MOODS["conversational"])
    # Piper treats each input line as a separate utterance/output file.
    # Send one complete utterance, retaining punctuation and every word.
    processed_text = " ".join(text.split())

    cmd = [
        str(PIPER_BIN),
        "--model",
        str(voice_model),
        "--length_scale",
        params["length_scale"],
        "--sentence_silence",
        params["sentence_silence"],
        "--output_file",
        str(out_file),
    ]

    # Publish only a complete WAV; concurrent readers must never see partial audio.
    with tempfile.NamedTemporaryFile(suffix=".wav", dir=out_file.parent, delete=False) as handle:
        pending = Path(handle.name)
    cmd[-1] = str(pending)
    try:
        result = subprocess.run(
            cmd,
            input=processed_text.encode("utf-8"),
            capture_output=True,
            timeout=SYNTHESIS_TIMEOUT_SECONDS,
            check=False,
        )

        if result.returncode != 0:
            err = result.stderr.decode("utf-8", errors="ignore")
            raise HTTPException(status_code=500, detail=f"Piper failed: {err[:300]}")

        with wave.open(str(pending), "rb") as audio:
            if audio.getnframes() == 0:
                raise HTTPException(status_code=500, detail="Piper returned empty audio")
        pending.replace(out_file)

    except subprocess.TimeoutExpired as exc:
        raise HTTPException(
            status_code=504,
            detail=f"Piper synthesis timed out after {SYNTHESIS_TIMEOUT_SECONDS}s",
        ) from exc
    finally:
        pending.unlink(missing_ok=True)


def wav_duration_ms(path: Path) -> int:
    """Read exact playback duration from a WAV header."""
    with wave.open(str(path), "rb") as reader:
        return int(round(reader.getnframes() / float(reader.getframerate()) * 1000))


def concat_wavs(paths: list[Path], out_file: Path) -> None:
    """Concatenate compatible WAV files without re-encoding them."""
    output = io.BytesIO()
    writer = None
    expected_format = None
    try:
        for path in paths:
            with wave.open(str(path), "rb") as reader:
                audio_format = (
                    reader.getnchannels(),
                    reader.getsampwidth(),
                    reader.getframerate(),
                    reader.getcomptype(),
                )
                if expected_format is None:
                    expected_format = audio_format
                    writer = wave.open(output, "wb")
                    writer.setnchannels(reader.getnchannels())
                    writer.setsampwidth(reader.getsampwidth())
                    writer.setframerate(reader.getframerate())
                    writer.setcomptype(reader.getcomptype(), reader.getcompname())
                elif audio_format != expected_format:
                    raise HTTPException(status_code=500, detail="Piper returned incompatible WAV segments")
                writer.writeframes(reader.readframes(reader.getnframes()))
    finally:
        if writer is not None:
            writer.close()

    out_file.write_bytes(output.getvalue())


@app.get("/")
async def root():
    return {
        "name": "MoStar Voice API",
        "engine": "piper",
        "voice": VOICE_NAME,
        "seal": SEAL,
        "routes": ["/health", "/speak", "/narrate", "/speak/verify", "/voices", "/moods", "/cleanup"],
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
    model_ok = Path(VOICES[VOICE_NAME]["model"]).exists()

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
                "id": voice_id,
                "engine": "piper",
                "label": entry["label"],
                "model": entry["model"],
                "status": "available" if Path(entry["model"]).exists() else "missing",
            }
            for voice_id, entry in VOICES.items()
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

    voice_id, voice_model = resolve_voice(req.voice)

    cache_str = f"natural-v2|{text_to_speak}|{req.mood}|{voice_id}|{speaker or chr(0)}|{req.moment_id or chr(0)}"
    digest = hashlib.sha256(cache_str.encode("utf-8")).hexdigest()[:16]
    out_file = AUDIO_OUT / f"woo-{digest}.wav"

    cached = out_file.exists()
    started = time.monotonic()

    if not cached:
        await run_in_threadpool(synthesize, text_to_speak, req.mood, voice_model, out_file)

    synthesis_ms = int((time.monotonic() - started) * 1000)
    duration_ms = wav_duration_ms(out_file)

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
        voice=voice_id,
        cached=cached,
        mood=req.mood,
        speaker=speaker,
        persona=speaker or voice_id,
        text_spoken=text_to_speak,
        seal=SEAL,
        duration_ms=duration_ms,
        synthesis_ms=synthesis_ms,
        request_id=digest,
    )
    return response.model_dump()


@app.post("/narrate", response_model=NarrateResponse)
async def narrate(req: NarrateRequest):
    """Synthesize measured segments and return their exact playback cues."""
    if req.mood not in MOODS:
        raise HTTPException(status_code=400, detail=f"Invalid mood: {req.mood}")

    segments = [text.strip() for text in req.segments]
    if any(not text for text in segments):
        raise HTTPException(status_code=400, detail="Narration segments must not be empty")

    voice_id, voice_model = resolve_voice(req.voice)
    # Key on the segment list itself, not a joined string: the cues file records
    # per-segment boundaries, so two different segmentations of the same words
    # must not share a digest.
    cache_str = f"narration-v2|{json.dumps(segments, ensure_ascii=False)}|{req.mood}|{voice_id}"
    digest = hashlib.sha256(cache_str.encode("utf-8")).hexdigest()[:16]
    out_file = AUDIO_OUT / f"narration-{digest}.wav"
    cues_file = AUDIO_OUT / f"narration-{digest}.cues.json"
    started = time.monotonic()

    measured: list[NarrationSegment] = []
    cursor = 0

    if not out_file.exists() or not cues_file.exists():
        with tempfile.TemporaryDirectory(prefix="mostar-narration-") as temp_dir:
            paths: list[Path] = []
            for index, text in enumerate(segments):
                path = Path(temp_dir) / f"segment-{index}.wav"
                await run_in_threadpool(synthesize, text, req.mood, voice_model, path)
                paths.append(path)
                span = wav_duration_ms(path)
                measured.append(
                    NarrationSegment(text=text, start_ms=cursor, end_ms=cursor + span)
                )
                cursor += span
            await run_in_threadpool(concat_wavs, paths, out_file)
        cues_file.write_text(
            json.dumps([segment.model_dump() for segment in measured]),
            encoding="utf-8",
        )
    else:
        measured = [
            NarrationSegment.model_validate(item)
            for item in json.loads(cues_file.read_text(encoding="utf-8"))
        ]

    synthesis_ms = int((time.monotonic() - started) * 1000)
    audio_ms = wav_duration_ms(out_file)
    # WAV rounding can differ by a millisecond across joined chunks. The
    # complete file is the final authority for the ceremony duration.
    if measured:
        measured[-1].end_ms = audio_ms

    return NarrateResponse(
        ok=True,
        audio_url=f"/audio/{out_file.name}",
        audio_ms=audio_ms,
        synthesis_ms=synthesis_ms,
        segments=measured,
        engine="piper",
        voice=voice_id,
        request_id=digest,
    )


@app.api_route("/speak/verify", methods=["GET", "POST"], response_model=None)
async def speak_verify():
    started = time.monotonic()
    piper_ok = PIPER_BIN.exists()
    model_ok = Path(VOICES[VOICE_NAME]["model"]).exists()
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
        await run_in_threadpool(
            synthesize, "Runtime ready.", "stable", Path(VOICES[VOICE_NAME]["model"]), out_file
        )
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
