"""
MoStar Grid — API Surface
FastAPI application with WebSocket support for live chat.

Port: 41010 (sovereign band)
"""
import logging
import sys
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from typing import Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from grid.config import GRID_HOST, GRID_PORT, SEAL_GLYPH
from grid.orchestrator import CommitFailedError, CommitForbiddenError, GridOrchestrator
from dcx import DCXLayer

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
    yield
    await orchestrator.shutdown()


# ── FastAPI App ────────────────────────────────────────────────────
app = FastAPI(
    title="MoStar Grid",
    description="Sovereign African Living Intelligence",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend
FRONTEND_DIR = PROJECT_ROOT / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


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


class RejectRequest(BaseModel):
    proposal_id: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=1, max_length=5000)


class ReviseRequest(BaseModel):
    proposal_id: str = Field(..., min_length=1)
    corrections: str = Field(..., min_length=1, max_length=20000)


# ── Routes ─────────────────────────────────────────────────────────

@app.get("/")
async def root():
    """Serve the chat UI or return identity."""
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {
        "name": "MoStar Grid",
        "version": "2.0.0",
        "status": "online",
        "seal": SEAL_GLYPH,
        "ui": "no frontend/index.html found — API-only mode",
    }


@app.get("/api/status")
async def get_status():
    """Full system status."""
    return await orchestrator.status()


@app.get("/api/health")
async def health():
    """Simple health check."""
    return {
        "status": "alive",
        "mindgraph": orchestrator.mindgraph.connected,
        "dcx": orchestrator.dcx.connected,
        "cycles": orchestrator.provenance.total_cycles,
        "seal": SEAL_GLYPH,
    }


@app.post("/api/think")
async def think(req: ThinkRequest):
    """
    Execute a full Talk → Learn → Remember cycle.
    The core intelligence endpoint.
    """
    return JSONResponse(
        status_code=410,
        content={
            "error": "gone",
            "message": "Phase 4.0a disables /api/think direct-write cycles. Use /api/propose.",
            "seal": SEAL_GLYPH,
        },
    )


@app.post("/api/learn")
async def learn(req: LearnRequest):
    """Manually inject knowledge into the graph."""
    return JSONResponse(
        status_code=410,
        content={
            "error": "gone",
            "message": "Phase 4.0a disables direct learning. Use /api/propose and human approval.",
            "seal": SEAL_GLYPH,
        },
    )


@app.post("/api/propose")
async def propose(req: ProposeRequest):
    proposal = await orchestrator.propose(req.canon_input)
    return proposal.to_dict()


@app.get("/api/proposals")
async def proposals(limit: int = 50, state: Optional[str] = None):
    if state == "pending":
        records = await orchestrator.approval_queue.list_pending()
    else:
        records = await orchestrator.approval_queue.list_all(limit=limit)
    return {"proposals": [record.to_dict() for record in records]}


@app.get("/api/proposals/{proposal_id}")
async def proposal_detail(proposal_id: str):
    try:
        record = await orchestrator.approval_queue.get(proposal_id)
    except KeyError as exc:
        raise HTTPException(404, str(exc)) from exc
    return record.to_dict()


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
    return commit.to_dict()


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
    return record.to_dict()


@app.post("/api/revise")
async def revise(req: ReviseRequest):
    try:
        record = await orchestrator.revise(req.proposal_id, req.corrections)
    except KeyError as exc:
        raise HTTPException(404, str(exc)) from exc
    except CommitForbiddenError as exc:
        raise HTTPException(409, str(exc)) from exc
    return record.to_dict()


@app.get("/api/density")
async def density():
    snapshot = await orchestrator.density.snapshot()
    readiness = await orchestrator.density.check_promotion_readiness()
    return {
        **snapshot.to_dict(),
        "promotion_ready": readiness["ready"],
        "promotion_gaps": readiness["gaps"],
    }


@app.get("/api/soul")
async def soul():
    """Who is this intelligence?"""
    return orchestrator.soul.to_dict()


@app.get("/api/agents")
async def agents():
    """List all sovereign agents in the graph."""
    if not orchestrator.mindgraph.connected:
        raise HTTPException(503, "MindGraph not connected")
    return await orchestrator.mindgraph.get_agents()


@app.get("/api/provenance")
async def provenance(n: int = 20):
    """Recent intelligence cycles."""
    return {
        "total": orchestrator.provenance.total_cycles,
        "recent": orchestrator.provenance.recent(n),
    }


@app.get("/api/moscripts")
async def moscripts():
    """List all registered MoScript contracts."""
    return orchestrator.moscript.list_scripts()


# ── WebSocket Chat ─────────────────────────────────────────────────

@app.websocket("/ws/chat")
async def websocket_chat(ws: WebSocket):
    """Live chat via WebSocket."""
    await ws.accept()
    await ws.send_json({
        "error": "gone",
        "message": "Phase 4.0a disables WebSocket chat direct-write cycles. Use /api/propose.",
        "seal": SEAL_GLYPH,
    })
    await ws.close(code=1008)


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
