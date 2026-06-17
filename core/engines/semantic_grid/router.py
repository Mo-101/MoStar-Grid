"""
Semantic Grid — Router
The one entry point: SemanticGrid.interpret().

This is the brain. It runs before the mouth opens.

  Human input
      ↓
  extract_layers() — LLM parse of all five layers
      ↓
  weight_advisors() — who should speak?
      ↓
  choose_persona() — how should MoStar be?
      ↓
  humor_level() / warmth_level() — tone calibration
      ↓
  TruthEngine.evaluate() — is this safe to respond to?
      ↓
  WooInterpreter.interpret() — symbolic state
      ↓
  SemanticFrame — the full meaning envelope, ready for a model
"""
from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from .contracts import SemanticFrame, SemanticState
from .layers import extract_layers
from .advisors import weight_advisors
from .personality import choose_persona
from .humor import humor_level, warmth_level
from .state import SemanticStateManager

logger = logging.getLogger("semantic_grid.router")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256_short(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


class SemanticGrid:
    """
    The Semantic Intelligence Layer.

    Stands between human signal and machine response.
    Interprets intent, governs meaning, remembers soulprint,
    weighs mission, selects persona — and only then allows the system to speak.
    """

    def __init__(
        self,
        ollama_url: str = "http://localhost:11434",
        model: str = "phi4:latest",
        neo4j_uri: str | None = None,
        enable_truth_engine: bool = True,
        enable_woo: bool = True,
    ):
        self._ollama_url = ollama_url
        self._model = model
        self._state_manager = SemanticStateManager(uri=neo4j_uri)
        self._enable_truth = enable_truth_engine
        self._enable_woo = enable_woo

        # Lazy-loaded to avoid import errors if engines aren't on path
        self._truth: Any = None
        self._woo: Any = None
        self._truth_loaded = False
        self._woo_loaded = False

    def _get_truth(self):
        if not self._truth_loaded:
            try:
                from truth_engine import TruthEngine
                self._truth = TruthEngine()
            except Exception:
                self._truth = None
            self._truth_loaded = True
        return self._truth

    def _get_woo(self):
        if not self._woo_loaded:
            try:
                # Use the sync symbolic interpreter, not the async canon-ingestion one
                from woo.interpreter import WooInterpreter as _WooInterp
                self._woo = _WooInterp()
            except Exception:
                self._woo = None
            self._woo_loaded = True
        return self._woo

    async def interpret(
        self,
        raw_input: str,
        user_id: str = "anonymous",
        source: str = "text",
        persist: bool = True,
    ) -> SemanticFrame:
        """
        Full interpretation pipeline.

        Args:
            raw_input: The raw user text.
            user_id:   Who is speaking.
            source:    "text" | "voice" | "event" | "gesture"
            persist:   Whether to write state and event to Neo4j.

        Returns:
            SemanticFrame with all layers, weights, persona, and policy populated.
        """
        frame_id = f"sf_{uuid.uuid4().hex[:12]}"

        # ── 1. Extract five semantic layers ───────────────────────────
        layers, extraction_source = await extract_layers(
            raw_input,
            ollama_url=self._ollama_url,
            model=self._model,
        )

        frame = SemanticFrame(
            raw_input=raw_input,
            user_id=user_id,
            source=source,
            literal=layers.get("literal", {}),
            operational=layers.get("operational", {}),
            human=layers.get("human", {}),
            mission=layers.get("mission", {}),
            soulprint=layers.get("soulprint", {}),
            frame_id=frame_id,
            created_at=_now(),
            extraction_source=extraction_source,
        )

        # ── 2. Weight advisors ────────────────────────────────────────
        combined_text = " ".join([
            raw_input,
            frame.operational.get("domain", ""),
            frame.mission.get("mission", ""),
            frame.soulprint.get("need", ""),
        ])
        frame.advisor_weights = weight_advisors(
            combined_text,
            domain=frame.operational.get("domain"),
        )

        # ── 3. Persona ────────────────────────────────────────────────
        frame.persona = choose_persona(frame)

        # ── 4. Tone calibration ───────────────────────────────────────
        frame.humor_level = humor_level(frame)
        warmth = warmth_level(frame)

        frame.response_policy = {
            "warmth": warmth,
            "clarity": 1.0,
            "humor": frame.humor_level,
            "risk_mode": (
                "careful"
                if frame.mission.get("priority") in {"high", "critical"}
                else "normal"
            ),
        }

        # ── 5. TruthEngine gate ───────────────────────────────────────
        truth = self._get_truth() if self._enable_truth else None
        if truth is not None:
            try:
                verdict = truth.evaluate(
                    response=raw_input,
                    query=frame.operational.get("problem", raw_input),
                    context_count=len(frame.advisor_weights),
                )
                frame.truth_passed = verdict.passed
            except Exception as exc:
                logger.warning("TruthEngine evaluation failed: %s", exc)
                frame.truth_passed = None
        else:
            frame.truth_passed = None

        # ── 6. Woo symbolic state ─────────────────────────────────────
        woo = self._get_woo() if self._enable_woo else None
        if woo is not None:
            try:
                interpretation = woo.interpret(raw_input)
                frame.woo_state = interpretation.symbolic_state
            except Exception as exc:
                logger.warning("Woo interpretation failed: %s", exc)
                frame.woo_state = None
        else:
            frame.woo_state = None

        # ── 7. Persist to Neo4j ───────────────────────────────────────
        if persist:
            self._persist_state(frame)

        logger.info(
            "SemanticFrame %s | persona=%s | advisors=%s | truth=%s | woo=%s",
            frame_id,
            frame.persona,
            list(frame.advisor_weights.keys())[:3],
            frame.truth_passed,
            frame.woo_state,
        )
        return frame

    def _persist_state(self, frame: SemanticFrame) -> None:
        """Update SemanticState and log the SemanticEvent."""
        try:
            # Build updated state from frame
            existing = self._state_manager.load(frame.user_id)
            urgency_map = {"low": 2, "medium": 5, "high": 8, "critical": 10}
            urgency_level = urgency_map.get(
                frame.mission.get("priority", "medium").lower(), 5
            )
            state = SemanticState(
                user_id=frame.user_id,
                current_mission=frame.mission.get("mission") or (
                    existing.current_mission if existing else None
                ),
                current_emotion=frame.human.get("emotion") or (
                    existing.current_emotion if existing else None
                ),
                urgency_level=urgency_level,
                trust_level=existing.trust_level if existing else 0.5,
                decision_mode=frame.soulprint.get("need", "observer"),
                focus_area=frame.operational.get("domain") or (
                    existing.focus_area if existing else None
                ),
            )
            self._state_manager.save(state)
            self._state_manager.log_event(
                frame_id=frame.frame_id,
                user_id=frame.user_id,
                raw_input_hash=_sha256_short(frame.raw_input),
            )
        except Exception as exc:
            logger.warning("State persistence failed (non-fatal): %s", exc)

    def close(self):
        self._state_manager.close()
