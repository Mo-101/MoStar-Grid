"""
Semantic Grid API
POST /api/semantic/interpret   — full five-layer interpretation
POST /api/semantic/state       — read current SemanticState for a user
GET  /api/semantic/advisors    — list available soul advisors
GET  /api/semantic/personas    — persona descriptions
"""
from __future__ import annotations

import logging
from pathlib import Path
import sys

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Resolve path so semantic_grid is importable
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
for _p in [
    str(_PROJECT_ROOT),
    str(_PROJECT_ROOT / "core" / "engines"),
    str(_PROJECT_ROOT / "core" / "sovereignty"),
    str(_PROJECT_ROOT / "core" / "protocols"),
    str(_PROJECT_ROOT / "back" / "services"),
]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from semantic_grid import (
    SemanticGrid,
    SOUL_ADVISORS,
    persona_voice_sample,
)
from semantic_grid.state import SemanticStateManager
from grid.config import OLLAMA_BASE_URL, DCX0_MODEL

logger = logging.getLogger("semantic_api")
router = APIRouter(prefix="/api/semantic", tags=["semantic-grid"])

# Module-level grid instance — shared with the main API
_grid = SemanticGrid(
    ollama_url=OLLAMA_BASE_URL,
    model=DCX0_MODEL,
)
_state_manager = SemanticStateManager()


# ── Request / Response models ─────────────────────────────────────────────────

class InterpretRequest(BaseModel):
    user_id: str = Field(default="anonymous", description="Who is speaking")
    input: str = Field(..., description="Raw human input text")
    source: str = Field(default="text", description="text | voice | event")
    persist: bool = Field(default=True, description="Write state to Neo4j")


class StateRequest(BaseModel):
    user_id: str


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/interpret")
async def interpret(req: InterpretRequest):
    """
    Full semantic interpretation pipeline.

    Takes raw human input and returns the complete SemanticFrame:
    five layers of meaning, advisor weights, persona, tone policy.
    """
    try:
        frame = await _grid.interpret(
            raw_input=req.input,
            user_id=req.user_id,
            source=req.source,
            persist=req.persist,
        )
        return JSONResponse({
            "ok": True,
            "semantic_frame": frame.to_dict(),
            "state_update": {
                "urgency_level": frame.mission.get("priority"),
                "focus_area": frame.operational.get("domain"),
                "emotion": frame.human.get("emotion"),
                "mission": frame.mission.get("mission"),
            },
            "persona": frame.persona,
            "advisor_weights": frame.advisor_weights,
            "response_policy": frame.response_policy,
        })
    except Exception as exc:
        logger.error("SemanticGrid.interpret failed: %s", exc)
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=500)


@router.post("/state")
async def get_state(req: StateRequest):
    """Return the current SemanticState for a user."""
    state = _state_manager.load(req.user_id)
    if state is None:
        return JSONResponse({
            "ok": True,
            "state": None,
            "message": f"No state found for user '{req.user_id}'",
        })
    return JSONResponse({"ok": True, "state": state.to_dict()})


@router.get("/advisors")
async def list_advisors():
    """List all soul advisors with their specialties and triggers."""
    return JSONResponse({
        "ok": True,
        "advisors": {
            name: {
                "specialty": cfg["specialty"],
                "trigger_sample": cfg["triggers"][:5],
            }
            for name, cfg in SOUL_ADVISORS.items()
        },
    })


@router.get("/personas")
async def list_personas():
    """Describe the six MoStar personas with voice samples."""
    personas = ["COMMANDER", "ARCHITECT", "TEACHER", "GUARDIAN", "COMPANION", "ORACLE"]
    return JSONResponse({
        "ok": True,
        "personas": {p: persona_voice_sample(p) for p in personas},
    })
