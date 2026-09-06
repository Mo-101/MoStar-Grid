"""
Semantic Grid — State Manager
Per-user SemanticState persisted to Neo4j.

Durable meaning goes to the graph.
Transient interpretation stays in memory.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from cypher_guard import get_guarded_sync_driver
from .contracts import SemanticState

logger = logging.getLogger("semantic_grid.state")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class SemanticStateManager:
    """
    Read and write SemanticState nodes in Neo4j.
    Falls back gracefully if Neo4j is unavailable.
    """

    def __init__(self, uri: str | None = None, auth: tuple[str, str] | None = None):
        if uri is None or auth is None:
            from grid.config import NEO4J_URI, NEO4J_USER, get_neo4j_password
            uri = uri if uri is not None else NEO4J_URI
            auth = auth if auth is not None else (NEO4J_USER, get_neo4j_password())
        self._uri = uri
        self._auth = auth
        self._driver = None

    def _connect(self):
        if self._driver is None:
            try:
                self._driver = get_guarded_sync_driver(
                    self._uri, auth=self._auth, allow_write=True
                )
            except Exception as exc:
                logger.warning("SemanticStateManager: Neo4j unavailable (%s)", exc)
        return self._driver

    def load(self, user_id: str) -> SemanticState | None:
        driver = self._connect()
        if driver is None:
            return None
        try:
            with driver.session() as session:
                record = session.run(
                    """
                    MATCH (s:SemanticState {user_id: $user_id})
                    RETURN s
                    ORDER BY s.updated_at DESC
                    LIMIT 1
                    """,
                    user_id=user_id,
                ).single()
                if record:
                    node = dict(record["s"])
                    return SemanticState(
                        user_id=node["user_id"],
                        current_mission=node.get("current_mission"),
                        current_emotion=node.get("current_emotion"),
                        urgency_level=int(node.get("urgency_level", 0)),
                        trust_level=float(node.get("trust_level", 0.5)),
                        decision_mode=node.get("decision_mode", "observer"),
                        focus_area=node.get("focus_area"),
                        updated_at=str(node.get("updated_at", "")),
                    )
        except Exception as exc:
            logger.warning("SemanticStateManager.load failed: %s", exc)
        return None

    def save(self, state: SemanticState) -> bool:
        driver = self._connect()
        if driver is None:
            return False
        try:
            now = _now()
            with driver.session() as session:
                session.run(
                    """
                    MERGE (s:SemanticState {user_id: $user_id})
                    SET s.current_mission = $current_mission,
                        s.current_emotion = $current_emotion,
                        s.urgency_level    = $urgency_level,
                        s.trust_level      = $trust_level,
                        s.decision_mode    = $decision_mode,
                        s.focus_area       = $focus_area,
                        s.updated_at       = $updated_at
                    """,
                    user_id=state.user_id,
                    current_mission=state.current_mission,
                    current_emotion=state.current_emotion,
                    urgency_level=state.urgency_level,
                    trust_level=state.trust_level,
                    decision_mode=state.decision_mode,
                    focus_area=state.focus_area,
                    updated_at=now,
                ).consume()
            return True
        except Exception as exc:
            logger.warning("SemanticStateManager.save failed: %s", exc)
            return False

    def log_event(self, frame_id: str, user_id: str, raw_input_hash: str) -> bool:
        """Persist a SemanticEvent node for the audit trail."""
        driver = self._connect()
        if driver is None:
            return False
        try:
            now = _now()
            with driver.session() as session:
                session.run(
                    """
                    MERGE (e:SemanticEvent {event_id: $frame_id})
                    SET e.user_id         = $user_id,
                        e.raw_input_hash  = $raw_input_hash,
                        e.created_at      = $created_at,
                        e.source          = 'semantic_grid',
                        e.provenance_status = 'interpreted'
                    WITH e
                    MATCH (s:SemanticState {user_id: $user_id})
                    MERGE (e)-[:UPDATED_STATE]->(s)
                    """,
                    frame_id=frame_id,
                    user_id=user_id,
                    raw_input_hash=raw_input_hash,
                    created_at=now,
                ).consume()
            return True
        except Exception as exc:
            logger.warning("SemanticStateManager.log_event failed: %s", exc)
            return False

    def close(self):
        if self._driver:
            self._driver.close()
            self._driver = None
