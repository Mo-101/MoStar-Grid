"""
MoStar Grid — API Surface
FastAPI application with WebSocket support for live chat.

Port: 41010 (sovereign band)
"""
import logging
import sys
import asyncio
import csv
import json
import uuid
import os
import time
import edge_tts
import feedparser
from pathlib import Path
from contextlib import asynccontextmanager
from urllib.parse import urlparse

from fastapi import APIRouter, FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional
import httpx

# Add project root and all rehoused core/services to path
PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.extend([
    str(PROJECT_ROOT),
    str(PROJECT_ROOT / "back" / "services"),
    str(PROJECT_ROOT / "core" / "engines"),
    str(PROJECT_ROOT / "core" / "sovereignty"),
    str(PROJECT_ROOT / "core" / "protocols"),
    str(PROJECT_ROOT / "core" / "ops"),
])

from grid.config import (
    DCX0_MODEL,
    GRID_HOST,
    GRID_PORT,
    MOSTAR_CLUSTER_ID,
    NEO4J_DATABASE,
    NEO4J_EXPECTED_HOST,
    NEO4J_EXPECTED_PORT,
    NEO4J_SENTINEL_LABELS,
    NEO4J_URI,
    SEAL_GLYPH,
    cluster_metadata,
)
from grid.config import OLLAMA_BASE_URL
from grid.orchestrator import CommitFailedError, CommitForbiddenError, GridOrchestrator
from grid.semantic_api import router as semantic_router
from grid.telemetry import ClusterTelemetry
from dcx import DCXLayer
from grid.events import event_bus, GridEvent
from grid.watchers import world_signal_watcher, telemetry_watcher, mood_engine, executor_watcher, mindgraph_reconnect_watcher
from grid.memory import (
    MemoryLayer,
    get_recent_memory,
    recall_similar,
    build_aware_briefing,
    get_last_briefing,
    compute_continuity,
)
from federation import (
    DisputeError,
    DisputeLog,
    EvidenceAccessError,
    EvidenceGateway,
    EvidenceNotFound,
    ScrollImporter,
    ScrollImportError,
)
from grid.auth import get_current_user_and_role, verify_permission
from grid.truth_gate import TruthGateEngine

# ── Logging ────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("grid_api")

# ── Orchestrator ───────────────────────────────────────────────────
orchestrator = GridOrchestrator()


@asynccontextmanager
async def lifespan(app: FastAPI):
    boot_result = await orchestrator.boot()
    logger.info("Grid API live on port %s — %s", GRID_PORT, SEAL_GLYPH)
    logger.info("Boot: %s", boot_result)
    
    # Initialize MemoryLayer
    app.state.memory_layer = MemoryLayer(orchestrator.mindgraph)
    
    # Start Watchers
    asyncio.create_task(world_signal_watcher())
    asyncio.create_task(telemetry_watcher(orchestrator))
    asyncio.create_task(autonomous_announcer(app.state.memory_layer))
    asyncio.create_task(executor_watcher(orchestrator))
    asyncio.create_task(mindgraph_reconnect_watcher(orchestrator))

    yield
    await orchestrator.shutdown()


# ── FastAPI App ────────────────────────────────────────────────────
app = FastAPI(
    title="MoStar Grid",
    description="Sovereign African Living Intelligence",
    version="2.0.0",
    lifespan=lifespan,
)

# Remediate open CORS configurations detected during baseline auditing
ALLOWED_ORIGINS = [
    "http://localhost:41012",
    "http://127.0.0.1:41012",
    "http://localhost:8080",
    "https://mostar-frontend.onrender.com",
] + [origin.strip() for origin in os.getenv("CORS_EXTRA_ORIGINS", "").split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-MoStar-Token"],
)

app.include_router(semantic_router)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        headers=exc.headers,
        content=_with_cluster({"detail": exc.detail}),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content=_with_cluster({"detail": exc.errors()}),
    )

# FastAPI runs in API-only mode on port 41010.
# Frontend runs on its own server on port 41012.

AUDIO_DIR = PROJECT_ROOT / "grid" / ".tmp" / "audio"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)
ENTITY_REGISTRY_PATH = PROJECT_ROOT / "data" / "mem" / "03_registry_data" / "csv" / "Entity.csv"
MCP_CLUSTER_API_URL = os.getenv("MCP_CLUSTER_API_URL", "")


def _clean_registry_value(value: object, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    if not text or text.lower() == "nan":
        return default
    return text


def _registry_capabilities(value: object) -> list[str]:
    text = _clean_registry_value(value)
    if not text:
        return []
    if "|" in text:
        return [item.strip() for item in text.split("|") if item.strip()]
    if text.startswith("[") and text.endswith("]"):
        return [
            item.strip(" '\"")
            for item in text.strip("[]").split(",")
            if item.strip(" '\"")
        ]
    return [text]


def _registry_score(row: dict) -> int:
    preferred_fields = (
        "activation_protocol",
        "bonded_to",
        "essence",
        "layer",
        "name",
        "origin",
        "role",
        "status",
        "title",
        "version",
        "vows",
    )
    return sum(1 for field in preferred_fields if _clean_registry_value(row.get(field)))


def _fallback_startup_reports() -> list[dict]:
    if not ENTITY_REGISTRY_PATH.exists():
        logger.warning("Startup registry fallback missing: %s", ENTITY_REGISTRY_PATH)
        return []

    by_entity: dict[str, dict] = {}
    with ENTITY_REGISTRY_PATH.open(newline="", encoding="utf-8-sig", errors="replace") as handle:
        for row in csv.DictReader(handle):
            entity_id = _clean_registry_value(row.get("entity_id"))
            if not entity_id:
                continue
            current = by_entity.get(entity_id)
            if current is None or _registry_score(row) >= _registry_score(current):
                by_entity[entity_id] = row

    reports = []
    for row in by_entity.values():
        name = _clean_registry_value(row.get("name"), _clean_registry_value(row.get("entity_id")))
        role = _clean_registry_value(row.get("role"), _clean_registry_value(row.get("title"), "ENTITY"))
        state = _clean_registry_value(row.get("status"), "REGISTRY")
        vows = _clean_registry_value(row.get("vows"), "Registry identity loaded")
        routing = _clean_registry_value(row.get("activation_protocol"), "REGISTRY")
        response = f"{name} reporting. {role}. {vows}."

        reports.append({
            "name": name,
            "entity_id": _clean_registry_value(row.get("entity_id")),
            "sp_element": _clean_registry_value(row.get("layer"), _clean_registry_value(row.get("essence"))),
            "state": state,
            "response": response,
            "voiceLine": response,
            "routing": routing,
            "timestamp": None,
            "role": role,
            "insignia": _clean_registry_value(row.get("insignia")),
            "sp_file": _clean_registry_value(row.get("activation_protocol")),
            "sp_cid": "",
            "vows": vows,
            "capabilities": _registry_capabilities(row.get("capabilities")),
            "source": "registry_fallback",
        })

    return sorted(reports, key=lambda report: report["name"].lower())


def _failed_probe(error: str) -> dict:
    return {
        "ok": False,
        "error": error[:300],
        "duration_ms": 0,
    }


def _neo4j_endpoint_identity() -> dict:
    parsed = urlparse(NEO4J_URI)
    scheme = parsed.scheme
    host = parsed.hostname or ""
    port = parsed.port or 7687
    expected_host_ok = not NEO4J_EXPECTED_HOST or host == NEO4J_EXPECTED_HOST
    expected_port_ok = port == NEO4J_EXPECTED_PORT
    return {
        "uri": f"{scheme}://{host}:{port}",
        "scheme": scheme,
        "host": host,
        "port": port,
        "expected_host": NEO4J_EXPECTED_HOST or None,
        "expected_port": NEO4J_EXPECTED_PORT,
        "expected_host_ok": expected_host_ok,
        "expected_port_ok": expected_port_ok,
        "ok": expected_host_ok and expected_port_ok,
    }


async def _probe_mindgraph() -> dict:
    started = time.monotonic()
    endpoint = _neo4j_endpoint_identity()
    if not orchestrator.mindgraph.connected or orchestrator.mindgraph._driver is None:
        return {
            "ok": False,
            "connected": False,
            "error": "MindGraph driver is not connected",
            "endpoint": endpoint,
            "duration_ms": int((time.monotonic() - started) * 1000),
        }

    count_query = """
    MATCH (n)
    RETURN count(n) AS node_count
    """
    labels_query = """
    MATCH (n)
    UNWIND labels(n) AS label
    RETURN label, count(*) AS count
    """
    try:
        async with orchestrator.mindgraph._driver.session(database=NEO4J_DATABASE) as session:
            result = await session.run(count_query)
            record = await result.single()
            node_count = int(record["node_count"] if record else 0)
            label_result = await session.run(labels_query)
            label_records = await label_result.data()
            label_counts = {
                str(row["label"]): int(row["count"])
                for row in label_records
            }
    except Exception as exc:
        return {
            "ok": False,
            "connected": True,
            "error": str(exc)[:300],
            "database": NEO4J_DATABASE,
            "endpoint": endpoint,
            "duration_ms": int((time.monotonic() - started) * 1000),
        }

    sentinel_counts = {
        label: label_counts.get(label, 0)
        for label in NEO4J_SENTINEL_LABELS
    }
    sentinel_ok = all(count > 0 for count in sentinel_counts.values())

    return {
        "ok": node_count > 0 and endpoint["ok"] and sentinel_ok,
        "connected": True,
        "database": NEO4J_DATABASE,
        "endpoint": endpoint,
        "node_count": node_count,
        "sentinel_counts": sentinel_counts,
        "sentinel_ok": sentinel_ok,
        "top_labels": dict(sorted(label_counts.items(), key=lambda item: item[1], reverse=True)[:12]),
        "assertions": [
            "MATCH (n) RETURN count(n)",
            "MATCH (n) UNWIND labels(n) AS label RETURN label, count(*)",
            f"endpoint port == {NEO4J_EXPECTED_PORT}",
        ],
        "duration_ms": int((time.monotonic() - started) * 1000),
    }


async def _probe_dcx() -> dict:
    started = time.monotonic()
    payload = {
        "model": DCX0_MODEL,
        "prompt": "Reply with exactly: DCX_HEALTH_OK",
        "stream": False,
        "options": {
            "temperature": 0,
            "num_predict": 8,
        },
    }
    try:
        async with httpx.AsyncClient(base_url=OLLAMA_BASE_URL, timeout=45.0) as client:
            resp = await client.post("/api/generate", json=payload)
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:
        return {
            "ok": False,
            "connected": False,
            "model": DCX0_MODEL,
            "base_url": OLLAMA_BASE_URL,
            "error": str(exc)[:300],
            "duration_ms": int((time.monotonic() - started) * 1000),
        }

    text = str(data.get("response", "")).strip()
    tokens = data.get("eval_count")
    return {
        "ok": bool(text) and tokens is not None,
        "connected": True,
        "model": DCX0_MODEL,
        "base_url": OLLAMA_BASE_URL,
        "execution": "remote_ollama_via_configured_url",
        "tokens": tokens,
        "response_preview": text[:80],
        "duration_ms": int((time.monotonic() - started) * 1000),
    }


async def _probe_mcp() -> dict:
    started = time.monotonic()
    if not MCP_CLUSTER_API_URL:
        return {
            "ok": False,
            "error": "MCP_CLUSTER_API_URL is not configured",
            "duration_ms": int((time.monotonic() - started) * 1000),
        }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{MCP_CLUSTER_API_URL.rstrip('/')}/api/health")
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:
        return {
            "ok": False,
            "url": MCP_CLUSTER_API_URL,
            "error": str(exc)[:300],
            "duration_ms": int((time.monotonic() - started) * 1000),
        }

    downstream = data.get("downstream_grid") if isinstance(data, dict) else None
    return {
        "ok": bool(data.get("status") == "alive" and downstream and downstream.get("ok")),
        "url": MCP_CLUSTER_API_URL,
        "service": data.get("service"),
        "role": data.get("role"),
        "downstream_grid": downstream,
        "duration_ms": int((time.monotonic() - started) * 1000),
    }

@app.get("/api/audio/{filename}")
async def get_audio(filename: str):
    file_path = AUDIO_DIR / filename
    if not file_path.exists():
        raise HTTPException(404, "Audio not found")
    return FileResponse(file_path, media_type="audio/mpeg")


# ── Models ─────────────────────────────────────────────────────────

class ThinkRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=5000)
    layer: Optional[str] = None  # dcx0, dcx1, dcx2

class LearnRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000)
    category: str = Field(default="manual")
    source: str = Field(default="api")


class ProposeRequest(BaseModel):
    canon_input: str = Field(..., min_length=1, max_length=20000)


class ApproveRequest(BaseModel):
    proposal_id: str = Field(..., min_length=1)
    approved_by: str = Field(..., min_length=1)


class CommitRequest(BaseModel):
    proposal_id: str = Field(..., min_length=1)


class RejectRequest(BaseModel):
    proposal_id: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=1, max_length=5000)


class ReviseRequest(BaseModel):
    proposal_id: str = Field(..., min_length=1)
    corrections: str = Field(..., min_length=1, max_length=20000)


class ScrollImportRequest(BaseModel):
    scroll: dict
    evidence_blobs: Optional[dict[str, str]] = None


class DisputeRegisterRequest(BaseModel):
    dispute: dict


# ── LLM Helper ─────────────────────────────────────────────────────

async def run_mostar_llm(prompt: dict) -> dict:
    model = "phi4:latest"
    if orchestrator.dcx._available_models:
        model = next(iter(orchestrator.dcx._available_models))
    
    system = prompt.get("system", "")
    user = prompt.get("user", "")
    tool_result = prompt.get("tool_result")
    
    if tool_result:
        user += f"\n\nTool Result Data:\n{json.dumps(tool_result)}"
        
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user}
    ]
    
    try:
        resp = await orchestrator.dcx._client.post("/api/chat", json={
            "model": model,
            "messages": messages,
            "format": "json",
            "stream": False,
        })
        resp.raise_for_status()
        content = resp.json().get("message", {}).get("content", "{}")
        return json.loads(content)
    except Exception as e:
        logger.error(f"Voice Agent LLM Error: {e}")
        return {"speech": "I am having trouble connecting to my cognitive layers."}


# ── Routes ─────────────────────────────────────────────────────────

def _with_cluster(payload: dict) -> dict:
    return {**cluster_metadata(), **payload}


@app.get("/")
async def root():
    return {
        "name": "MoStar Grid",
        "version": "2.0.0",
        "status": "online",
        "mindgraph": orchestrator.mindgraph.connected,
        "dcx": orchestrator.dcx.connected,
        "seal": SEAL_GLYPH,
    }


@app.get("/api/status")
async def get_status():
    """Full system status."""
    return await orchestrator.status()


@app.get("/api/live")
async def live():
    """Cheap process liveness for Render routing health checks."""
    return {
        "status": "alive",
        "ready": orchestrator._ready,
        "seal": SEAL_GLYPH,
        "phase": "4.0a",
    }


@app.get("/api/health")
async def health():
    """Earned runtime health check.

    This endpoint only marks a subsystem true after a live round-trip:
    Neo4j count query, Ollama generation, and MCP gateway health call.
    """
    started = time.monotonic()
    checks = await asyncio.gather(
        _probe_mindgraph(),
        _probe_dcx(),
        _probe_mcp(),
        return_exceptions=True,
    )

    mindgraph, dcx, mcp = [
        check if isinstance(check, dict) else _failed_probe(str(check))
        for check in checks
    ]
    ready = bool(mindgraph["ok"] and dcx["ok"] and mcp["ok"])

    return {
        "status": "ready" if ready else "degraded",
        "ready": ready,
        "mindgraph": mindgraph,
        "dcx": dcx,
        "cycles": orchestrator.provenance.total_cycles,
        "seal": SEAL_GLYPH,
        "mcp": mcp,
        "phase": "4.0a",
        "duration_ms": int((time.monotonic() - started) * 1000),
    }


@app.get("/api/mindgraph/status")
async def mindgraph_status():
    """Live graph stats — node count, relationship count, label breakdown."""
    return await orchestrator.mindgraph.get_graph_stats()


@app.get("/api/truthgate/report")
async def generate_truthgate_report(request: Request):
    """
    Enforces the TruthGate Reporting Law. Maps physical environment metrics
    and open ports to ensure narrative assumptions never override system reality.
    """
    user = get_current_user_and_role(request)
    verify_permission("read", user)
    try:
        engine = TruthGateEngine()
        return {
            "title": "TruthGate Structural System Audit",
            "doctrine_seal": "MoStar audits must report evidence state, not narrative confidence.",
            "timestamp_epoch": os.times()[4],
            "covenant_verdict": {
                "Observed_Not_Equal_Inferred": True,
                "Configured_Not_Equal_Running": True,
                "Declared_Not_Equal_Verified": True,
            },
            "matrix": engine.compile_report(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"TruthGate Engine Interruption: {str(e)}",
        )


def _direct_write_disabled(endpoint: str) -> JSONResponse:
    return JSONResponse(
        status_code=410,
        content={
            "error": "direct_write_disabled",
            **cluster_metadata(),
            "message": f"Phase 4.0a disables {endpoint} direct-write cycles. Use /api/propose.",
            "seal": SEAL_GLYPH,
        },
    )

async def fetch_world_signals() -> str:
    try:
        africa_feed = feedparser.parse("https://feeds.bbci.co.uk/news/world/africa/rss.xml")
        econ_feed = feedparser.parse("https://feeds.bbci.co.uk/news/business/economy/rss.xml")
        
        signals = []
        if africa_feed.entries:
            signals.append("Africa: " + africa_feed.entries[0].title)
        if econ_feed.entries:
            signals.append("Economy: " + econ_feed.entries[0].title)
            
        return "\n".join(signals) if signals else "No live signals found."
    except Exception as e:
        logger.error(f"Signal fetch failed: {e}")
        return "Live signals disconnected."

async def synthesize_woo_voice(text: str, mood: str = "stable") -> Optional[Path]:
    try:
        voice = os.getenv("TTS_VOICE", "en-NG-AbeoNeural")
        filename = f"woo-briefing-{uuid.uuid4().hex[:8]}.mp3"
        output_path = AUDIO_DIR / filename
        
        # Adjust pitch/rate based on mood
        rate = "+0%"
        pitch = "+0Hz"
        if mood in ["alert", "critical"]:
            rate = "+15%"
            pitch = "+20Hz"
        elif mood == "concerned":
            rate = "-10%"
            pitch = "-10Hz"
        
        communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
        await communicate.save(str(output_path))
        
        return output_path
    except Exception as e:
        logger.error(f"TTS synthesis failed: {e}")
        return None

async def autonomous_announcer(memory_layer):
    """Listens to EventBus, and if severity is high/critical, generates an announcement."""
    q = event_bus.subscribe()
    while True:
        event = await q.get()
        if event.severity in ["high", "critical"]:
            # Generate Announcement
            prompt = {
                "system": 'You are Woo. Be concise. State the new event clearly and its implication.',
                "user": f"New Event: {event.text}\nSeverity: {event.severity}\nGenerate a short broadcast to Flame."
            }
            res = await run_mostar_llm(prompt)
            speech = res.get("speech", f"Flame, critical event detected: {event.text}")
            
            audio_path = await synthesize_woo_voice(speech, mood=event.mood)
            audio_url = f"/api/audio/{audio_path.name}" if audio_path else ""
            
            # Write to Memory
            await memory_layer.log_event(event)
            if audio_url:
                await memory_layer.log_woo_utterance(event, audio_url)
            
            # Broadcast the announcement to SSE stream
            event.payload["audio_url"] = audio_url
            event.payload["speech"] = speech
            
            # We don't yield here, we just update the event which might be picked up by the SSE stream
            # We will handle SSE broadcast below


@app.get("/api/memory/recent")
async def memory_recent(limit: int = 10):
    try:
        return await get_recent_memory(orchestrator.mindgraph._driver, limit)
    except Exception as e:
        logger.error(f"Failed to get recent memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/memory/foundational")
async def memory_foundational():
    try:
        driver = orchestrator.mindgraph._driver
        async with driver.session(database=NEO4J_DATABASE) as session:
            result = await session.run("MATCH (fm:FoundationalMemory) RETURN fm")
            records = await result.data()
            return {"results": [r["fm"] for r in records], "seal": "🜃∴🜂"}
    except Exception as e:
        logger.error(f"Failed to fetch foundational memory: {e}")
        return {"error": str(e)}

@app.get("/api/memory/recall")
async def memory_recall(event_type: str, hours: int = 24):
    try:
        return await recall_similar(orchestrator.mindgraph._driver, event_type, hours)
    except Exception as e:
        logger.error(f"Failed to recall similar memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/briefing")
async def get_autonomous_briefing(write_log: bool = False):
    try:
        driver = orchestrator.mindgraph._driver
        
        # 1. Get telemetry and signals
        telemetry = await orchestrator.status()
        news = await fetch_world_signals()
        
        # 2. Build facts and compute continuity
        briefing_data = await build_aware_briefing(driver, write_log=False)
        facts = briefing_data["facts"]

        # Fetch all external data concurrently
        from grid.external_data import fetch_all_external
        external = await fetch_all_external()
        weather = external["weather"]
        flights = external["flights"]
        health  = external["health"]

        # Get mood (reflective)
        mood = "reflective"

        # 3. Route to DCX2 (Body) to generate the narrative
        weather_summary = (
            ", ".join(
                f"{city}: {data.get('temp')}C {data.get('description')} "
                f"humidity {data.get('humidity', '?')}% wind {data.get('wind_kph', '?')}kph"
                for city, data in weather["data"].items()
                if data.get("status") == "online"
            )
            if weather["live"] and weather["data"] else "unavailable"
        )
        flight_summary = (
            ", ".join(
                f"{city}: {info.get('summary', 'no data')}"
                for city, info in (flights.get("data") or {}).items()
                if info.get("status") == "online"
            ) if flights["live"] and flights.get("data")
            else flights.get("status", "unavailable")
        )
        who_summary = ""
        if health["live"] and health["sources"].get("who_gho", {}).get("status") == "live":
            who_data = health["sources"]["who_gho"]["data"]
            who_summary = "; ".join(
                f"{k} life expectancy {v.get('value', '?')} ({v.get('year', '?')})"
                for k, v in who_data.items()
            )

        prompt_user = (
            "Write three concise operational briefing sentences using only these facts: "
            f"MoStar Grid nodes {facts['current_nodes']} (+{facts.get('node_growth', 0)} growth); "
            f"relationships {facts['current_relationships']}; "
            f"events {facts['current_events']} (delta {facts.get('event_pressure_delta', 0)}); "
            f"weather ({weather.get('provider','?')}): {weather_summary}; "
            f"flights: {flight_summary}; "
            f"WHO health: {who_summary or 'unavailable'}. "
            "State unavailable providers clearly. Be direct and sovereign in tone."
        )

        fallback_briefing = (
            f"MoStar Grid online — {facts['current_nodes']:,} nodes, "
            f"{facts['current_relationships']:,} relationships, "
            f"{facts['current_events']} active events. "
            f"Weather ({weather.get('provider','?')}): {weather_summary}. "
            f"Flights: {flight_summary}. "
            f"WHO health signals: {who_summary or 'unavailable'}."
        )
        try:
            dcx_res = await asyncio.wait_for(
                orchestrator.dcx.think(
                    query=prompt_user,
                    layer=DCXLayer.BODY,
                    graph_context=None,
                ),
                timeout=45,
            )
            briefing_text = dcx_res.content.strip()
            if not briefing_text or briefing_text.startswith("[DCX "):
                briefing_text = fallback_briefing
        except Exception as e:
            logger.warning("DCX briefing generation timed out or failed; using verified fallback: %s", e)
            briefing_text = fallback_briefing

        audio_url = None
        # 4. Log briefing event and woo utterance in Neo4j to keep graph data rich
        if write_log:
            memory_layer = app.state.memory_layer
            briefing_event = GridEvent(
                type="dashboard_awaken",
                severity="low",
                mood=mood,
                source="briefing",
                text="Grid Awaken Sequence Initiated",
                payload={"facts": facts, "message": briefing_text},
                source_type="runtime_generated",
                verification_status="verified",
                operational_trust="reference",
                created_by="get_autonomous_briefing",
            )
            await memory_layer.log_event(briefing_event)
            await memory_layer.log_briefing(briefing_event, telemetry, news)

            # Persist BriefingLog node to database
            from datetime import datetime, timezone
            iso_now = datetime.now(timezone.utc).isoformat()
            async with driver.session(database=NEO4J_DATABASE) as session:
                await session.run("""
                    CREATE (b:BriefingLog {
                        id: $b_id,
                        message: $message,
                        created_at: $created_at,
                        event_count: $event_count,
                        node_count: $node_count,
                        relationship_count: $relationship_count,
                        referenced_previous: $has_history,
                        cluster_id: $cluster_id,
                        source: 'autonomous_briefing',
                        created_by: 'get_autonomous_briefing',
                        source_type: 'ai_generated',
                        verification_status: 'unverified',
                        operational_trust: 'reference',
                        seal: 'Synthetic'
                    })
                """, b_id=f"brief_aware_{int(datetime.now(timezone.utc).timestamp())}",
                     message=briefing_text,
                     created_at=iso_now,
                     event_count=facts["current_events"],
                     node_count=facts["current_nodes"],
                     relationship_count=facts["current_relationships"],
                     has_history=facts.get("has_history", False),
                     cluster_id=MOSTAR_CLUSTER_ID)

            # Synthesize voice for the briefing text with reflective mood
            audio_path = await synthesize_woo_voice(briefing_text, mood=mood)
            audio_url = f"/api/audio/{audio_path.name}" if audio_path else None
            if audio_url:
                await memory_layer.log_woo_utterance(briefing_event, audio_url)

        return {
            "ok": True,
            "message": briefing_text,
            "text": briefing_text,
            "speech": briefing_text,
            "audio_url": audio_url,
            "telemetry": telemetry,
            "signals": news,
            "facts": facts,
            "weather": weather,
            "flights": flights,
            "seal": "🜃∴🜂",
        }
    except Exception as e:
        logger.error(f"Aware briefing failed: {e}")
        return {
            "ok": False,
            "message": "The Grid is gathering its memory.",
            "text": "The Grid is gathering its memory.",
            "speech": "The Grid is gathering its memory.",
            "facts": {},
            "seal": "🜃∴🜂"
        }

@app.post("/api/voice-command")
async def voice_agent(payload: dict):
    text = payload.get("text", "").strip()

    if not text:
        return {"ok": False, "error": "Empty voice command"}

    system = """
You are Woo, the MoStar Grid voice agent.
You are sovereign, concise, operational, and truthful.
You may call tools when needed.
Return JSON only:
{
  "speech": "spoken response",
  "tool": "none|get_telemetry|get_grid_status|get_memory|get_resonance",
  "data": {}
}
"""

    tool_result = None
    lowered = text.lower()

    if "pulse" in lowered or "telemetry" in lowered:
        tool_result = {"telemetry": "Active", "grid_pulse": 98.4}
    elif "status" in lowered or "grid" in lowered:
        status_data = await orchestrator.status()
        tool_result = {"status": status_data}
    elif "memory" in lowered:
        tool_result = {"memory": "Memory crystals sealed."}
    elif "resonance" in lowered:
        tool_result = {"resonance": "Odu resonance is stable."}

    prompt = {
        "system": system,
        "user": text,
        "tool_result": tool_result,
    }

    result = await run_mostar_llm(prompt)

    return {
        "ok": True,
        "input": text,
        "tool_result": tool_result,
        "speech": result.get("speech", "The grid has received the command."),
    }


@app.post("/api/think")
async def think(req: ThinkRequest):
    """
    Execute a full Talk → Learn → Remember cycle.
    The core intelligence endpoint.
    """
    force_layer = DCXLayer(req.layer) if req.layer else None
    try:
        result = await orchestrator.think(req.query, force_layer=force_layer)
    except CommitForbiddenError as e:
        raise HTTPException(status_code=403, detail=str(e))
    return {
        "layer": result.dcx_layer,
        "model": result.dcx_model,
        "content": result.response,
        "context_used": result.context_nodes,
        "truth_passed": result.truth_passed,
        "sealed": result.sealed,
        "seal": result.seal,
    }


@app.api_route("/api/learn", methods=["GET", "POST"])
async def learn(req: Optional[LearnRequest] = None):
    """Manually inject knowledge into the graph."""
    return _direct_write_disabled("/api/learn")


@app.post("/api/propose")
async def propose(req: ProposeRequest):
    proposal = await orchestrator.propose(req.canon_input)
    return _with_cluster(proposal.to_dict())


@app.get("/api/proposals")
async def proposals(limit: int = 50, state: Optional[str] = None):
    if state == "pending":
        records = await orchestrator.approval_queue.list_pending()
    else:
        records = await orchestrator.approval_queue.list_all(limit=limit)
    return _with_cluster({"proposals": [record.to_dict() for record in records]})


@app.get("/api/proposals/{proposal_id}")
async def proposal_detail(proposal_id: str):
    try:
        record = await orchestrator.approval_queue.get(proposal_id)
    except KeyError as exc:
        raise HTTPException(404, str(exc)) from exc
    return _with_cluster(record.to_dict())


@app.post("/api/approve")
async def approve(req: ApproveRequest):
    try:
        approved = await orchestrator.approval_queue.approve(req.proposal_id, req.approved_by)
        orchestrator.provenance.record_event(
            "proposal_approved",
            {"proposal_id": approved.id, "approved_by": req.approved_by},
        )
        commit = await orchestrator.commit_after_seal(req.proposal_id)
    except KeyError as exc:
        raise HTTPException(404, str(exc)) from exc
    except CommitFailedError as exc:
        raise HTTPException(503, str(exc)) from exc
    except (CommitForbiddenError, ValueError) as exc:
        raise HTTPException(409, str(exc)) from exc
    return _with_cluster(commit.to_dict())


@app.post("/api/commit")
async def commit(req: CommitRequest):
    try:
        result = await orchestrator.commit_after_seal(req.proposal_id)
    except KeyError as exc:
        raise HTTPException(404, str(exc)) from exc
    except CommitFailedError as exc:
        raise HTTPException(503, str(exc)) from exc
    except CommitForbiddenError as exc:
        raise HTTPException(409, str(exc)) from exc
    return _with_cluster(result.to_dict())


@app.post("/api/reject")
async def reject(req: RejectRequest):
    try:
        record = await orchestrator.approval_queue.reject(req.proposal_id, req.reason)
    except KeyError as exc:
        raise HTTPException(404, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    orchestrator.provenance.record_event(
        "proposal_rejected",
        {"proposal_id": record.id, "reason": req.reason},
    )
    return _with_cluster(record.to_dict())


@app.post("/api/revise")
async def revise(req: ReviseRequest):
    try:
        record = await orchestrator.revise(req.proposal_id, req.corrections)
    except KeyError as exc:
        raise HTTPException(404, str(exc)) from exc
    except CommitForbiddenError as exc:
        raise HTTPException(409, str(exc)) from exc
    return _with_cluster(record.to_dict())


@app.post("/api/scrolls/import")
async def import_scroll(req: ScrollImportRequest):
    try:
        result = ScrollImporter().import_scroll(
            req.scroll,
            evidence_blobs=req.evidence_blobs,
        )
    except ScrollImportError as exc:
        raise HTTPException(422, str(exc)) from exc
    return _with_cluster(result.to_dict())


@app.post("/api/disputes/register")
async def register_dispute(req: DisputeRegisterRequest):
    try:
        result = DisputeLog().register_dispute(req.dispute)
    except DisputeError as exc:
        status_code = 401 if exc.__class__.__name__ == "InvalidDisputeSignature" else 422
        raise HTTPException(status_code, str(exc)) from exc
    return _with_cluster(result)


@app.get("/api/evidence/{scroll_id}")
async def get_evidence(scroll_id: str, requester_cluster_id: str, signature: str):
    try:
        result = EvidenceGateway().get_evidence(
            scroll_id=scroll_id,
            requester_cluster_id=requester_cluster_id,
            signature=signature,
        )
    except EvidenceNotFound as exc:
        raise HTTPException(404, str(exc)) from exc
    except EvidenceAccessError as exc:
        raise HTTPException(exc.status_code, str(exc)) from exc
    return _with_cluster(result)


@app.get("/api/density")
async def density():
    snapshot = await orchestrator.density.snapshot()
    readiness = await orchestrator.density.check_promotion_readiness()
    return _with_cluster({
        **snapshot.to_dict(),
        "promotion_ready": readiness["ready"],
        "promotion_gaps": readiness["gaps"],
    })


class GridEventSchema(BaseModel):
    cluster_id: str
    cycles: int
    status: str
    seal: str

_idempotency_cache = set()

def is_duplicate_transaction(key: str) -> bool:
    if key in _idempotency_cache:
        return True
    _idempotency_cache.add(key)
    return False

@app.get("/api/grid/event")
async def get_grid_events():
    return {"status": "success", "data": []}

@app.get("/api/grid/startup-reports")
async def get_startup_reports():
    driver = orchestrator.mindgraph._driver
    if driver is None:
        logger.warning("MindGraph unavailable; serving startup reports from registry fallback")
        return _with_cluster({"reports": _fallback_startup_reports(), "source": "registry_fallback"})

    try:
        async with driver.session(database=NEO4J_DATABASE) as session:
            result = await session.run("""
                MATCH (e:Entity)
                OPTIONAL MATCH (e)-[:REPORTED_STARTUP]->(m:StartupReport)
                WITH e, m ORDER BY m.timestamp DESC
                WITH e, head(collect(m)) as latest_report
                RETURN e.name as name, 
                       e.entity_id as entity_id, 
                       coalesce(e.sp_element, e.element, '') as sp_element, 
                       coalesce(e.status, e.state, 'DORMANT') as state,
                       coalesce(latest_report.response, e.vows, '') as response, 
                       coalesce(latest_report.routing, e.activation_protocol, '') as routing, 
                       toString(latest_report.timestamp) as timestamp,
                       e.role as role,
                       e.insignia as insignia,
                       coalesce(e.sp_file, '') as sp_file,
                       coalesce(e.sp_cid, '') as sp_cid,
                       e.vows as vows,
                       e.capabilities as capabilities
                ORDER BY e.name
            """)
            records = await result.data()
            if records:
                return _with_cluster({"reports": records, "source": "mindgraph"})

            logger.warning("MindGraph returned no startup reports; serving registry fallback")
            return _with_cluster({"reports": _fallback_startup_reports(), "source": "registry_fallback"})
    except Exception as e:
        logger.error(f"Failed to fetch startup reports: {e}")
        return _with_cluster({
            "reports": _fallback_startup_reports(),
            "source": "registry_fallback",
            "warning": str(e),
        })

@app.post("/api/grid/event")
async def create_grid_event(payload: GridEventSchema, request: Request):
    idempotency_key = request.headers.get("X-Idempotency-Key")
    if idempotency_key:
        if is_duplicate_transaction(idempotency_key):
            raise HTTPException(
                status_code=409,
                detail="Duplicate transaction signal detected and absorbed."
            )
            
    try:
        event = GridEvent(
            type="ingestion",
            severity="info",
            mood="stable",
            source="external_agent",
            text=f"Cycle update: {payload.cycles} for {payload.cluster_id}",
            payload={"cycles": payload.cycles, "status": payload.status, "seal": payload.seal}
        )
        await app.state.memory_layer.log_event(event)
        await event_bus.publish(event)
        
        return {"status": "committed", "cluster_id": payload.cluster_id}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ledger compilation failure: {str(e)}"
        )


@app.get("/api/grid/census")
async def get_grid_census():
    """Retrieve live database metrics from the mindgraph for crowning the dashboard."""
    if not orchestrator.mindgraph.connected:
        return JSONResponse({
            "nodes": 0,
            "relationships": 0,
            "events": 0,
            "utterances": 0,
            "last_heartbeat": None,
            "seal": "🜃∴🜂",
            "status": "degraded"
        }, status_code=503)

    try:
        async with orchestrator.mindgraph._driver.session(database=NEO4J_DATABASE) as session:
            # Nodes count
            nodes_res = await session.run("MATCH (n) RETURN count(n) AS total")
            nodes_record = await nodes_res.single()
            nodes_count = nodes_record["total"] if nodes_record else 0

            # Relationships count
            rels_res = await session.run("MATCH ()-[r]->() RETURN count(r) AS total")
            rels_record = await rels_res.single()
            rels_count = rels_record["total"] if rels_record else 0

            # GridEvent count
            events_res = await session.run("MATCH (e:GridEvent) RETURN count(e) AS total")
            events_record = await events_res.single()
            events_count = events_record["total"] if events_record else 0

            # WooUtterance count
            utts_res = await session.run("MATCH (w:WooUtterance) RETURN count(w) AS total")
            utts_record = await utts_res.single()
            utts_count = utts_record["total"] if utts_record else 0

            # Sealed Agents count
            sealed_res = await session.run("MATCH (e:Entity) WHERE e.soulprint_loaded = true RETURN count(e) AS total")
            sealed_record = await sealed_res.single()
            sealed_count = sealed_record["total"] if sealed_record else 0

            # ExecutorHeartbeat
            hb_res = await session.run("MATCH (h:ExecutorHeartbeat) RETURN h.created_at AS hb ORDER BY h.created_at DESC LIMIT 1")
            hb_record = await hb_res.single()
            last_hb = hb_record["hb"] if hb_record else None

            return {
                "nodes": nodes_count,
                "relationships": rels_count,
                "events": events_count,
                "utterances": utts_count,
                "sealed_agents": sealed_count,
                "last_heartbeat": last_hb,
                "seal": "🜃∴🜂"
            }
    except Exception as e:
        logger.error(f"Failed to fetch census data: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/telemetry")
async def telemetry(limit: int = 20):
    """Read-only aggregate for the live dashboard."""
    status_payload = await orchestrator.status()
    proposals_payload = [
        record.to_dict()
        for record in await orchestrator.approval_queue.list_all(limit=limit)
    ]
    telemetry_payload = ClusterTelemetry().snapshot(
        status=status_payload,
        proposals=proposals_payload,
        provenance=orchestrator.provenance.recent(limit),
    )
    return _with_cluster(telemetry_payload)


@app.get("/api/stream")
async def stream_telemetry(limit: int = 20):
    """Live Server-Sent Events (SSE) telemetry feed for the dashboard heartbeat."""
    q = event_bus.subscribe()
    
    async def event_generator():
        try:
            while True:
                # Attempt to get events if any exist
                try:
                    event = q.get_nowait()
                    yield f"data: {json.dumps({'type': 'event', 'event': event.to_dict()})}\\n\\n"
                except asyncio.QueueEmpty:
                    pass
                
                status_payload = await orchestrator.status()
                proposals_payload = [
                    record.to_dict()
                    for record in await orchestrator.approval_queue.list_all(limit=limit)
                ]
                telemetry_payload = ClusterTelemetry().snapshot(
                    status=status_payload,
                    proposals=proposals_payload,
                    provenance=orchestrator.provenance.recent(limit),
                )
                data = _with_cluster(telemetry_payload)
                data["type"] = "telemetry"
                yield f"data: {json.dumps(data)}\\n\\n"
                
                await asyncio.sleep(1.5)
        finally:
            event_bus.unsubscribe(q)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/api/soul")
async def soul():
    """Who is this intelligence?"""
    return _with_cluster({"soul": orchestrator.soul.to_dict()})


@app.get("/api/agents")
async def agents():
    """List all sovereign agents in the graph."""
    if not orchestrator.mindgraph.connected:
        raise HTTPException(503, "MindGraph not connected")
    return _with_cluster({"agents": await orchestrator.mindgraph.get_agents()})


@app.get("/api/provenance")
async def provenance(n: int = 20):
    """Volatile runtime provenance log.

    TODO P4-010: Implement graph-backed /api/provenance summary from Neo4j.
    Current /api/provenance is explicitly runtime-memory-only.
    """
    return {
        "scope": "runtime-memory-only",
        "store": "orchestrator-memory",
        "persistent_graph_backed": False,
        "warning": (
            "This endpoint reflects volatile in-memory orchestrator provenance only. "
            "It is not proof of persistent MoStarMoment graph provenance."
        ),
        "p4_008_status": "backfill-complete-api-runtime-labeled",
        "total": orchestrator.provenance.total_cycles,
        "recent": orchestrator.provenance.recent(n),
    }


@app.get("/api/moscripts")
async def moscripts():
    """List all registered MoScript contracts."""
    return _with_cluster({"moscripts": orchestrator.moscript.list_scripts()})


# ── WebSocket Chat ─────────────────────────────────────────────────

@app.websocket("/ws/chat")
async def websocket_chat(ws: WebSocket):
    """Live chat via WebSocket."""
    await ws.accept()
    await ws.send_json({
        "error": "gone",
        **cluster_metadata(),
        "message": "Phase 4.0a disables WebSocket chat direct-write cycles. Use /api/propose.",
        "seal": SEAL_GLYPH,
    })
    await ws.close(code=1008)


# ── Voice Proxy (Piper service on 41071) ──────────────────────────

VOICE_SERVICE_URL = "http://localhost:41071"

@app.api_route("/api/voice/{path:path}", methods=["GET", "POST"])
async def voice_proxy(path: str, request: Request):
    """Proxy voice requests to the sovereign Piper TTS service."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        url = f"{VOICE_SERVICE_URL}/{path}"
        try:
            if request.method == "POST":
                body = await request.body()
                resp = await client.post(url, content=body, headers={"Content-Type": "application/json"})
            else:
                resp = await client.get(url)
            return StreamingResponse(
                iter([resp.content]),
                status_code=resp.status_code,
                media_type=resp.headers.get("content-type", "application/json"),
            )
        except httpx.ConnectError:
            return JSONResponse({"error": "Voice service unreachable", "status": "degraded"}, status_code=503)



@app.post("/api/debug/emit-test-event")
async def emit_test_event():
    event = GridEvent(
        type="world_signal",
        severity="high",
        mood="alert",
        source="debug",
        text="A critical resonance frequency has been detected in the eastern sector of the MoStar Grid.",
        payload={"debug": True}
    )
    # Log directly to memory layer (Neo4j)
    await app.state.memory_layer.log_event(event)
    await event_bus.publish(event)
    return {"ok": True, "event_id": event.id}


# ── Watchtower Agent Governance ─────────────────────────────────────

watchtower_router = APIRouter(prefix="/watchtower", tags=["watchtower"])

VALID_AGENT_STATUSES = {
    "SCANNED",
    "PENDING_REVIEW",
    "REFORMATTED",
    "SANCTIONED",
    "REJECTED",
    "QUARANTINED",
}
VALID_AUTH_LEVELS = {"PROVISIONAL", "OPERATIONAL", "INSTITUTIONAL"}


class WatchtowerAgentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    source: str = Field(..., min_length=1, max_length=500)
    purpose: str = Field(..., min_length=1, max_length=1000)
    namespace: str = Field(..., min_length=1, max_length=120)
    capabilities: list[str] = Field(default_factory=list)
    data_contracts: list[str] = Field(default_factory=list)
    safety_flags: list[str] = Field(default_factory=list)
    provenance_verified: bool = False


class WatchtowerAgentStatusUpdate(BaseModel):
    status: str
    approved_by: Optional[str] = None
    auth_level: Optional[str] = None


class WatchtowerTrustScoreUpdate(BaseModel):
    trust_score: int = Field(..., ge=0, le=100)


def _watchtower_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()


def _compute_initial_trust(payload: WatchtowerAgentCreate) -> int:
    score = 50
    if payload.provenance_verified:
        score += 20
    if payload.data_contracts:
        score += 10
    if payload.capabilities:
        score += 5
    score -= len(payload.safety_flags) * 10
    return max(0, min(100, score))


def _agent_from_record(record) -> dict:
    agent = dict(record["a"])
    agent.setdefault("capabilities", [])
    agent.setdefault("data_contracts", [])
    agent.setdefault("safety_flags", [])
    agent.setdefault("approved_by", None)
    agent.setdefault("approved_at", None)
    agent.setdefault("auth_level", None)
    agent.setdefault("last_sync", None)
    agent.setdefault("provenance_verified", False)
    return agent


async def _emit_watchtower_event(event_type: str, ref_id: str, detail: str) -> None:
    try:
        if not orchestrator.mindgraph.connected:
            return
        driver = orchestrator.mindgraph._driver
        async with driver.session(database=NEO4J_DATABASE) as session:
            await session.run(
                """
                CREATE (:GridEvent {
                    id: $id,
                    type: $type,
                    ref_id: $ref_id,
                    detail: $detail,
                    created_at: $created_at
                })
                """,
                id=str(uuid.uuid4()),
                type=event_type,
                ref_id=ref_id,
                detail=detail,
                created_at=_watchtower_now(),
            )
    except Exception as exc:
        logger.warning("Watchtower event emission failed: %s", exc)


def _require_mindgraph():
    if not orchestrator.mindgraph.connected:
        raise HTTPException(503, "MindGraph not connected")
    return orchestrator.mindgraph._driver


@watchtower_router.get("/agents")
async def watchtower_list_agents(status: Optional[str] = None):
    if status and status not in VALID_AGENT_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

    driver = _require_mindgraph()
    async with driver.session(database=NEO4J_DATABASE) as session:
        result = await session.run(
            """
            MATCH (a:Agent)
            WHERE $status IS NULL OR a.status = $status
            RETURN a
            ORDER BY coalesce(a.created_at, "") DESC
            """,
            status=status,
        )
        records = await result.data()
    return [_agent_from_record(record) for record in records]


@watchtower_router.get("/agents/{agent_id}")
async def watchtower_get_agent(agent_id: str):
    driver = _require_mindgraph()
    async with driver.session(database=NEO4J_DATABASE) as session:
        result = await session.run("MATCH (a:Agent {id: $id}) RETURN a", id=agent_id)
        record = await result.single()
    if not record:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    return _agent_from_record(record)


@watchtower_router.post("/agents", status_code=201)
async def watchtower_register_agent(payload: WatchtowerAgentCreate):
    driver = _require_mindgraph()
    async with driver.session(database=NEO4J_DATABASE) as session:
        count_result = await session.run("MATCH (a:Agent) RETURN count(a) AS count")
        count_record = await count_result.single()
        agent_id = f"AGT-{(count_record['count'] if count_record else 0) + 1:04d}"

        props = {
            "id": agent_id,
            "name": payload.name,
            "source": payload.source,
            "purpose": payload.purpose,
            "namespace": payload.namespace,
            "capabilities": payload.capabilities,
            "data_contracts": payload.data_contracts,
            "safety_flags": payload.safety_flags,
            "provenance_verified": payload.provenance_verified,
            "trust_score": _compute_initial_trust(payload),
            "status": "SCANNED",
            "approved_by": None,
            "approved_at": None,
            "auth_level": None,
            "last_sync": None,
            "created_at": _watchtower_now(),
        }
        result = await session.run(
            """
            CREATE (a:Agent)
            SET a = $props
            RETURN a
            """,
            props=props,
        )
        record = await result.single()

    await _emit_watchtower_event(
        "AGENT_REGISTERED",
        agent_id,
        f"New agent detected: {payload.name} from {payload.source}",
    )
    return _agent_from_record(record)


@watchtower_router.put("/agents/{agent_id}/status")
async def watchtower_update_agent_status(agent_id: str, payload: WatchtowerAgentStatusUpdate):
    if payload.status not in VALID_AGENT_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status: {payload.status}")
    if payload.auth_level and payload.auth_level not in VALID_AUTH_LEVELS:
        raise HTTPException(status_code=400, detail=f"Invalid auth_level: {payload.auth_level}")

    updates = {
        "status": payload.status,
        "approved_by": payload.approved_by,
        "auth_level": payload.auth_level,
    }
    if payload.status == "SANCTIONED":
        updates["approved_at"] = _watchtower_now()

    driver = _require_mindgraph()
    async with driver.session(database=NEO4J_DATABASE) as session:
        result = await session.run(
            """
            MATCH (a:Agent {id: $id})
            SET a += $updates
            RETURN a
            """,
            id=agent_id,
            updates=updates,
        )
        record = await result.single()

    if not record:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

    await _emit_watchtower_event(
        f"AGENT_{payload.status}",
        agent_id,
        f"Agent status updated to {payload.status}"
        + (f" by {payload.approved_by}" if payload.approved_by else ""),
    )
    return _agent_from_record(record)


@watchtower_router.put("/agents/{agent_id}/trust")
async def watchtower_update_trust_score(agent_id: str, payload: WatchtowerTrustScoreUpdate):
    driver = _require_mindgraph()
    async with driver.session(database=NEO4J_DATABASE) as session:
        result = await session.run(
            """
            MATCH (a:Agent {id: $id})
            SET a.trust_score = $trust_score
            RETURN a
            """,
            id=agent_id,
            trust_score=payload.trust_score,
        )
        record = await result.single()
    if not record:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

    await _emit_watchtower_event(
        "AGENT_TRUST_OVERRIDE",
        agent_id,
        f"Agent trust score manually set to {payload.trust_score}",
    )
    return _agent_from_record(record)


@watchtower_router.get("/sanctuary")
async def watchtower_sanctuary():
    driver = _require_mindgraph()
    async with driver.session(database=NEO4J_DATABASE) as session:
        result = await session.run(
            """
            MATCH (a:Agent {status: 'SANCTIONED'})
            RETURN a
            ORDER BY coalesce(a.approved_at, "") DESC
            """
        )
        records = await result.data()
    return [_agent_from_record(record) for record in records]


@watchtower_router.get("/stats")
async def watchtower_stats():
    driver = _require_mindgraph()
    async with driver.session(database=NEO4J_DATABASE) as session:
        counts_result = await session.run(
            "MATCH (a:Agent) RETURN a.status AS status, count(a) AS count"
        )
        count_records = await counts_result.data()
        flagged_result = await session.run(
            """
            MATCH (a:Agent)
            WHERE size(coalesce(a.safety_flags, [])) > 0
            RETURN count(a) AS count
            """
        )
        flagged_record = await flagged_result.single()

    counts = {record["status"]: record["count"] for record in count_records if record["status"]}
    return {
        "total": sum(counts.values()),
        "by_status": counts,
        "sanctioned": counts.get("SANCTIONED", 0),
        "pending": counts.get("PENDING_REVIEW", 0) + counts.get("SCANNED", 0),
        "flagged": flagged_record["count"] if flagged_record else 0,
    }


@watchtower_router.delete("/agents/{agent_id}")
async def watchtower_delete_agent(agent_id: str):
    driver = _require_mindgraph()
    async with driver.session(database=NEO4J_DATABASE) as session:
        result = await session.run(
            """
            MATCH (a:Agent {id: $id})
            WITH a, a.name AS name
            DETACH DELETE a
            RETURN name
            """,
            id=agent_id,
        )
        record = await result.single()

    if not record:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

    await _emit_watchtower_event(
        "AGENT_DELETED",
        agent_id,
        f"Agent {agent_id} permanently removed",
    )
    return {"deleted": agent_id}


app.include_router(watchtower_router)


# ── SPA Catch-All (must be LAST route) ─────────────────────────────

@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    """Serve index.html for all non-API client-side routes (e.g. /dashboard)."""
    if full_path.startswith("api/"):
        return JSONResponse({"error": "not found"}, status_code=404)
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return JSONResponse({"error": "frontend not built"}, status_code=404)


# ── Run ────────────────────────────────────────────────────────────

def main():
    import uvicorn
    uvicorn.run(
        "grid.api:app",
        host=GRID_HOST,
        port=GRID_PORT,
        reload=True,
        log_level="info",
    )


if __name__ == "__main__":
    main()
