"""16A2: parameterized live telemetry queries and Neon persistence adapter."""

from __future__ import annotations

import hashlib
import json
import math
import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[3] / ".env")


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class EventSeverity(Enum):
    INFO = 0.1
    WARN = 0.5
    ELEVATED = 1.0
    RESTRICTED = 2.0
    LOCKED = 5.0


class MetricSource(Enum):
    GRAPH_AUDIT_EVENT = 1
    AGENT_RUN_LOG = 2
    DECISION_RUN_LOG = 3
    MOSCRIPT_REGISTRY = 4
    WOO_INTERPRETATION_LOG = 5


@dataclass
class TelemetryQuery:
    query_id: str
    sql: str
    params: Dict[str, Any]
    source: MetricSource
    timeout_ms: int
    explanation: str
    cached: bool = False
    cache_ttl_seconds: int = 0


class TelemetryQueryBuilder:
    """Build queries against the deployed Neon schema, never interpolating values."""

    def __init__(self, window_seconds: Optional[int] = None,
                 half_life_seconds: Optional[int] = None,
                 batch_size: Optional[int] = None,
                 query_timeout_ms: Optional[int] = None):
        self.window_seconds = window_seconds or int(os.getenv("RESONANCE_WINDOW_SECONDS", "3600"))
        self.half_life_seconds = half_life_seconds or int(os.getenv("RESONANCE_HALF_LIFE_SECONDS", "600"))
        self.batch_size = batch_size or int(os.getenv("TELEMETRY_BATCH_SIZE", "1000"))
        self.query_timeout_ms = query_timeout_ms or int(os.getenv("TELEMETRY_QUERY_TIMEOUT_MS", "5000"))

    def decay_factor(self, age_seconds: float) -> float:
        if age_seconds < 0:
            return 1.0
        # The locked 16A1 formula uses exp(-age/half_life).
        return math.exp(-age_seconds / self.half_life_seconds)

    def resonance_formula(self) -> str:
        return (
            "resonance_score = sum(event_weight * exp(-age_seconds / "
            f"{self.half_life_seconds})) / {self.window_seconds}"
        )

    def _window(self) -> Dict[str, Any]:
        end = utcnow()
        return {"window_start": end - timedelta(seconds=self.window_seconds),
                "window_end": end, "limit": self.batch_size}

    def _query(self, query_id: str, source: MetricSource, sql: str,
               explanation: str, params: Optional[Dict[str, Any]] = None) -> TelemetryQuery:
        return TelemetryQuery(query_id, sql, params or self._window(), source,
                              self.query_timeout_ms, explanation)

    def query_audit_events_by_type(self, event_type: str,
                                   component_id: Optional[str] = None,
                                   limit: Optional[int] = None) -> TelemetryQuery:
        params = self._window() | {"event_type": event_type, "limit": limit or self.batch_size}
        component_clause = ""
        if component_id:
            params["component_id"] = component_id
            component_clause = " AND entity_canonical_id = %(component_id)s"
        return self._query(
            f"audit_events_{event_type}_{component_id or 'all'}", MetricSource.GRAPH_AUDIT_EVENT,
            """SELECT id, event_type, entity_canonical_id AS component_id,
                      COALESCE(payload_json->>'source_level', status, 'INFO') AS source_level,
                      payload_json AS event_data, created_at, 1.0 AS count
                 FROM graph_audit_event
                WHERE event_type = %(event_type)s
                  AND created_at BETWEEN %(window_start)s AND %(window_end)s"""
            + component_clause + " ORDER BY created_at DESC LIMIT %(limit)s",
            "Live graph audit events in the rolling window.", params)

    def query_level_transitions(self, component_id: Optional[str] = None) -> TelemetryQuery:
        params = self._window()
        clause = ""
        if component_id:
            params["component_id"] = component_id
            clause = " AND entity_canonical_id = %(component_id)s"
        return self._query(
            f"level_transitions_{component_id or 'all'}", MetricSource.GRAPH_AUDIT_EVENT,
            """SELECT id, event_type, entity_canonical_id AS component_id,
                      payload_json->>'source_level' AS source_level,
                      payload_json->>'target_level' AS target_level,
                      payload_json AS event_data, created_at, 1.0 AS count
                 FROM graph_audit_event
                WHERE event_type IN ('CONTROL_PLANE_LEVEL_TRANSITION','CONTROL_PLANE_RELAXED')
                  AND created_at BETWEEN %(window_start)s AND %(window_end)s"""
            + clause + " ORDER BY created_at DESC LIMIT %(limit)s",
            "Live control-plane transitions in the rolling window.", params)

    def query_agent_failures(self, component_id: Optional[str] = None) -> TelemetryQuery:
        params = self._window()
        clause = ""
        if component_id:
            params["component_id"] = component_id
            clause = " AND agent_canonical_id = %(component_id)s"
        return self._query(
            f"agent_failures_{component_id or 'all'}", MetricSource.AGENT_RUN_LOG,
            """SELECT id, agent_canonical_id AS agent_id, status,
                      decision_summary_json AS details, created_at, 1.0 AS count
                 FROM agent_run_log
                WHERE upper(status) IN ('FAILED','ERROR','DENIED')
                  AND created_at BETWEEN %(window_start)s AND %(window_end)s"""
            + clause + " ORDER BY created_at DESC LIMIT %(limit)s",
            "Live failed agent runs in the rolling window.", params)

    def query_decision_delays(self, threshold_ms: int = 1000) -> TelemetryQuery:
        params = self._window() | {"threshold_ms": threshold_ms}
        return self._query(
            f"decision_delays_{threshold_ms}ms", MetricSource.DECISION_RUN_LOG,
            """SELECT id, run_canonical_id AS decision_id, status, result_json,
                      executed_at AS created_at,
                      CASE WHEN COALESCE(result_json->>'duration_ms','') ~ '^[0-9]+(\\.[0-9]+)?$'
                           THEN (result_json->>'duration_ms')::double precision ELSE 0 END AS duration_ms,
                      1.0 AS count
                 FROM decision_run_log
                WHERE executed_at BETWEEN %(window_start)s AND %(window_end)s
                  AND (CASE WHEN COALESCE(result_json->>'duration_ms','') ~ '^[0-9]+(\\.[0-9]+)?$'
                            THEN (result_json->>'duration_ms')::double precision ELSE 0 END) > %(threshold_ms)s
                ORDER BY duration_ms DESC LIMIT %(limit)s""",
            "Live decision runs whose recorded duration exceeds the threshold.", params)

    def query_moscript_errors(self) -> TelemetryQuery:
        return self._query(
            "moscript_errors", MetricSource.MOSCRIPT_REGISTRY,
            """SELECT id, canonical_id AS script_id, script_status AS execution_status,
                      metadata_json AS error_details, updated_at AS created_at, 1.0 AS count
                 FROM moscript_registry
                WHERE upper(script_status) IN ('ERROR','FAILED','DENIED')
                  AND updated_at BETWEEN %(window_start)s AND %(window_end)s
                ORDER BY updated_at DESC LIMIT %(limit)s""",
            "Live MoScript registry error states in the rolling window.")

    def query_woo_warnings(self) -> TelemetryQuery:
        return self._query(
            "woo_warnings", MetricSource.WOO_INTERPRETATION_LOG,
            """SELECT id, canonical_id AS woo_id, verdict AS interpretation_status,
                      explanation_json AS warning_details, resonance_score,
                      created_at, 1.0 AS count
                 FROM woo_interpretation_log
                WHERE upper(verdict) IN ('DENIED','WARNING','WARN','REJECTED')
                  AND created_at BETWEEN %(window_start)s AND %(window_end)s
                ORDER BY created_at DESC LIMIT %(limit)s""",
            "Live Woo warnings and denials in the rolling window.")

    def query_resonance_components(self) -> Dict[str, TelemetryQuery]:
        return {
            "audit_events_warn": self.query_audit_events_by_type("TELEMETRY_ALERT_RAISED"),
            "audit_events_elevated": self.query_audit_events_by_type("ANOMALY_TREND"),
            "audit_events_restricted": self.query_audit_events_by_type("CONTROL_PLANE_RESTRICTED"),
            "audit_events_locked": self.query_audit_events_by_type("CONTROL_PLANE_LOCKED"),
            "agent_failures": self.query_agent_failures(),
            "decision_delays": self.query_decision_delays(),
            "moscript_errors": self.query_moscript_errors(),
            "woo_warnings": self.query_woo_warnings(),
        }

    def query_current_resonance_state(self, component_id: str) -> TelemetryQuery:
        return self._query(
            f"current_resonance_{component_id}", MetricSource.GRAPH_AUDIT_EVENT,
            "SELECT * FROM control_plane_resonance_state WHERE component_id=%(component_id)s",
            "Persisted 16A control-plane resonance state.", {"component_id": component_id})

    def to_dict(self, query: TelemetryQuery) -> Dict[str, Any]:
        return {"query_id": query.query_id, "source": query.source.name,
                "timeout_ms": query.timeout_ms, "explanation": query.explanation,
                "sql": query.sql, "params": query.params}

    def explain(self, query: TelemetryQuery) -> str:
        return json.dumps(self.to_dict(query), indent=2, default=str)


class NeonTelemetryStore:
    """Synchronous Neon adapter used by 16A3, 16A4, and the verifier."""

    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or os.getenv("NEON_DATABASE_URL") or os.getenv("POSTGRES_URL_NON_POOLING") or os.getenv("POSTGRES_URL")
        if not self.database_url:
            raise RuntimeError("NEON_DATABASE_URL (or POSTGRES_URL) is required")
        self._connection = None

    def _connect(self):
        import psycopg
        if self._connection is None or self._connection.closed:
            self._connection = psycopg.connect(self.database_url, connect_timeout=10,
                                               autocommit=True)
        return self._connection

    def verify_connectivity(self) -> Dict[str, Any]:
        conn = self._connect()
        with conn.cursor() as cur:
            cur.execute("SELECT current_database(), current_schema()")
            database, schema = cur.fetchone()
        return {"backend": "neon", "database": database, "schema": schema}

    def ensure_runtime_schema(self) -> None:
        ddl = """CREATE TABLE IF NOT EXISTS control_plane_resonance_state (
            id UUID PRIMARY KEY,
            component_id TEXT NOT NULL UNIQUE,
            current_score DOUBLE PRECISION NOT NULL,
            level TEXT NOT NULL,
            contributing_events JSONB NOT NULL DEFAULT '[]'::jsonb,
            decay_reason TEXT,
            threshold_crossed_at TIMESTAMPTZ,
            last_computed TIMESTAMPTZ NOT NULL,
            previous_level TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )"""
        conn = self._connect()
        with conn.cursor() as cur:
            cur.execute(ddl)

    def execute(self, query: TelemetryQuery) -> List[Dict[str, Any]]:
        from psycopg.rows import dict_row
        conn = self._connect()
        with conn.cursor(row_factory=dict_row) as cur:
                cur.execute("SELECT set_config('statement_timeout', %s, false)",
                            (f"{query.timeout_ms}ms",))
                cur.execute(query.sql, query.params)
                return [dict(row) for row in cur.fetchall()]

    def execute_resonance_queries(self, builder: TelemetryQueryBuilder) -> Dict[str, List[Dict[str, Any]]]:
        return {name: self.execute(query) for name, query in builder.query_resonance_components().items()}

    @staticmethod
    def _json(value: Any) -> str:
        return json.dumps(value, default=str, sort_keys=True)

    def insert_audit(self, record: Dict[str, Any]) -> str:
        audit_id = str(uuid.uuid4())
        payload = dict(record)
        created_at = payload.pop("created_at", utcnow())
        component_id = str(payload.get("component_id") or "system")
        source = str(payload.get("created_by_component") or "16A")
        body = self._json(payload)
        digest = hashlib.sha256(body.encode()).hexdigest()
        sql = """INSERT INTO graph_audit_event
            (id,event_type,entity_type,entity_canonical_id,related_canonical_id,status,
             payload_json,content_hash,operator_id,environment,source_system,created_at)
            VALUES (%(id)s,%(event_type)s,'operational_hardening',%(component)s,
                    %(trace)s,%(status)s,%(payload)s::jsonb,%(hash)s,%(operator)s,
                    %(environment)s,%(source)s,%(created_at)s)"""
        params = {"id": audit_id, "event_type": record["event_type"],
                  "component": component_id, "trace": record.get("trace_id"),
                  "status": record.get("target_level") or record.get("source_level") or "INFO",
                  "payload": body, "hash": digest,
                  "operator": record.get("actor_id") or "system",
                  "environment": os.getenv("MOSTAR_ENV", os.getenv("ENVIRONMENT", "development")),
                  "source": source, "created_at": created_at}
        conn = self._connect()
        with conn.cursor() as cur:
            cur.execute(sql, params)
        return audit_id

    def get_audits(self, *, trace_id: Optional[str] = None,
                   component_id: Optional[str] = None) -> List[Dict[str, Any]]:
        from psycopg.rows import dict_row
        clauses, params = ["entity_type='operational_hardening'"], {}
        if trace_id:
            clauses.append("related_canonical_id=%(trace_id)s")
            params["trace_id"] = trace_id
        if component_id:
            clauses.append("entity_canonical_id=%(component_id)s")
            params["component_id"] = component_id
        sql = "SELECT * FROM graph_audit_event WHERE " + " AND ".join(clauses) + " ORDER BY created_at"
        conn = self._connect()
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(sql, params)
            return [dict(row) for row in cur.fetchall()]

    def get_state(self, component_id: str) -> Optional[Dict[str, Any]]:
        rows = self.execute(TelemetryQuery(
            "state", "SELECT * FROM control_plane_resonance_state WHERE component_id=%(component_id)s",
            {"component_id": component_id}, MetricSource.GRAPH_AUDIT_EVENT, 5000, "state"))
        return rows[0] if rows else None

    def upsert_state(self, component_id: str, score: float, level: str,
                     contributing_events: Optional[List[Dict[str, Any]]] = None,
                     decay_reason: Optional[str] = None,
                     previous_level: Optional[str] = None) -> None:
        now = utcnow()
        sql = """INSERT INTO control_plane_resonance_state
            (id,component_id,current_score,level,contributing_events,decay_reason,
             threshold_crossed_at,last_computed,previous_level,created_at,updated_at)
            VALUES (%(id)s,%(component)s,%(score)s,%(level)s,%(events)s::jsonb,%(reason)s,
                    %(crossed)s,%(now)s,%(previous)s,%(now)s,%(now)s)
            ON CONFLICT (component_id) DO UPDATE SET current_score=EXCLUDED.current_score,
                level=EXCLUDED.level, contributing_events=EXCLUDED.contributing_events,
                decay_reason=EXCLUDED.decay_reason,
                threshold_crossed_at=CASE WHEN control_plane_resonance_state.level<>EXCLUDED.level
                                          THEN EXCLUDED.last_computed ELSE control_plane_resonance_state.threshold_crossed_at END,
                last_computed=EXCLUDED.last_computed, previous_level=EXCLUDED.previous_level,
                updated_at=EXCLUDED.updated_at"""
        params = {"id": str(uuid.uuid4()), "component": component_id, "score": score,
                  "level": level, "events": self._json(contributing_events or []),
                  "reason": decay_reason, "crossed": now, "now": now,
                  "previous": previous_level}
        conn = self._connect()
        with conn.cursor() as cur:
            cur.execute(sql, params)

    def update_score_preserving_level(self, component_id: str, score: float,
                                      events: List[Dict[str, Any]]) -> None:
        state = self.get_state(component_id)
        level = state["level"] if state else "INFO"
        previous = state.get("previous_level") if state else None
        self.upsert_state(component_id, score, level, events, "rolling_window", previous)

    def cleanup_verifier_records(self, prefix: str) -> None:
        conn = self._connect()
        with conn.cursor() as cur:
            cur.execute("""DELETE FROM graph_audit_event
                            WHERE entity_type='operational_hardening'
                              AND (entity_canonical_id LIKE %(prefix)s
                                   OR related_canonical_id LIKE %(trace_prefix)s)""",
                        {"prefix": prefix + "%", "trace_prefix": "%" + prefix + "%"})
            cur.execute("DELETE FROM control_plane_resonance_state WHERE component_id LIKE %(prefix)s", {"prefix": prefix + "%"})


def main() -> None:
    builder = TelemetryQueryBuilder()
    store = NeonTelemetryStore()
    print(json.dumps({"connection": store.verify_connectivity(),
                      "row_counts": {k: len(v) for k, v in store.execute_resonance_queries(builder).items()}},
                     indent=2, default=str))


if __name__ == "__main__":
    main()
