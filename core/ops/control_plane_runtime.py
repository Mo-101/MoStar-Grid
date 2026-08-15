"""Runtime consumer for Phase 16A control-plane state."""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Protocol
from urllib.parse import parse_qs, urlparse

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "core" / "ops" / "config" / "enforcement_policy.yaml"
load_dotenv(ROOT / ".env")


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class RuntimeEnforcementDecision:
    trace_id: str
    surface: str
    component_id: str
    policy_branch: str
    operation: str
    level: str
    actions: list[str]
    allowed: bool
    reason: str
    evaluated_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class RuntimeEnforcementDenied(RuntimeError):
    def __init__(self, decision: RuntimeEnforcementDecision):
        self.decision = decision
        super().__init__(f"{decision.surface}/{decision.operation} denied at {decision.level}: {decision.reason}")


class EnforcementStateProvider(Protocol):
    def get_level(self, component_id: str) -> str: ...
    def audit(self, decision: RuntimeEnforcementDecision) -> str: ...


def validate_sovereign_database_url(database_url: str) -> None:
    """Reject any relational control plane outside the local host."""
    parsed = urlparse(database_url)
    if parsed.scheme not in {"postgresql", "postgres"}:
        raise RuntimeError("DATABASE_URL must use PostgreSQL")

    query = parse_qs(parsed.query)
    socket_host = query.get("host", [""])[0]
    local_socket = bool(socket_host) and Path(socket_host).is_absolute()
    if parsed.hostname not in {"127.0.0.1", "localhost", "::1", None}:
        raise RuntimeError("Grid sovereign DATABASE_URL must target local Postgres")
    if parsed.hostname is None and not local_socket:
        raise RuntimeError(
            "Grid sovereign DATABASE_URL must target localhost or a local Unix socket"
        )


class PostgresEnforcementStateProvider:
    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or os.getenv("DATABASE_URL")
        if not self.database_url:
            raise RuntimeError("DATABASE_URL is required")
        validate_sovereign_database_url(self.database_url)
        self._connection = None

    def connect(self):
        import psycopg
        if self._connection is None or self._connection.closed:
            self._connection = psycopg.connect(self.database_url, connect_timeout=10, autocommit=True)
        return self._connection

    def verify_schema(self) -> None:
        required = {"control_plane_resonance_state", "graph_audit_event"}
        with self.connect().cursor() as cur:
            cur.execute(
                """SELECT table_name FROM information_schema.tables
                   WHERE table_schema='public' AND table_name = ANY(%s)""",
                (list(required),),
            )
            present = {str(row[0]) for row in cur.fetchall()}
        missing = sorted(required - present)
        if missing:
            raise RuntimeError(
                "sovereign governance schema missing: " + ", ".join(missing)
            )

    def get_level(self, component_id: str) -> str:
        with self.connect().cursor() as cur:
            cur.execute("SELECT level FROM control_plane_resonance_state WHERE component_id=%s", (component_id,))
            row = cur.fetchone()
        return str(row[0]).upper() if row else "INFO"

    def audit(self, decision: RuntimeEnforcementDecision) -> str:
        audit_id = str(uuid.uuid4())
        body = json.dumps(decision.to_dict(), sort_keys=True, default=str)
        sql = """INSERT INTO graph_audit_event
            (id,event_type,entity_type,entity_canonical_id,related_canonical_id,status,
             payload_json,content_hash,operator_id,environment,source_system,created_at)
            VALUES (%s,%s,'runtime_enforcement',%s,%s,%s,%s::jsonb,%s,'system',%s,
                    '16B_runtime_enforcement',%s)"""
        params = (audit_id,
                  "RUNTIME_ENFORCEMENT_ALLOWED" if decision.allowed else "RUNTIME_ENFORCEMENT_DENIED",
                  decision.component_id, decision.trace_id, decision.level, body,
                  hashlib.sha256(body.encode()).hexdigest(),
                  os.getenv("MOSTAR_ENV", os.getenv("ENVIRONMENT", "development")), utcnow())
        with self.connect().cursor() as cur:
            cur.execute(sql, params)
        return audit_id


class RuntimeEnforcementGate:
    SURFACES = {
        "agents": ("agents", "agent_execution"),
        "mo_woo_nexus": ("mo_woo_nexus", "mo_woo_nexus"),
        "decision_engine": ("decision_engine", "decision_engine"),
        "moscript_registry": ("moscript_registry", "moscript_registry"),
    }

    def __init__(self, provider: Optional[EnforcementStateProvider] = None,
                 policy_path: Path | str = POLICY_PATH, enabled: Optional[bool] = None):
        self.provider = provider or PostgresEnforcementStateProvider()
        self.enabled = (os.getenv("ENFORCEMENT_ENABLED", "true").lower() == "true"
                        if enabled is None else enabled)
        with Path(policy_path).open(encoding="utf-8") as handle:
            document = yaml.safe_load(handle) or {}
        self.policy = document.get("policies", {})
        self.runtime_config = document.get("runtime_attachment", {})

    def connect(self) -> None:
        connect = getattr(self.provider, "connect", None)
        if connect is not None:
            connect()

    def verify_schema(self) -> None:
        verify = getattr(self.provider, "verify_schema", None)
        if verify is not None:
            verify()

    def evaluate(self, surface: str, operation: str,
                 context: Optional[Dict[str, Any]] = None) -> RuntimeEnforcementDecision:
        if surface not in self.SURFACES:
            raise ValueError(f"Unknown enforcement surface: {surface}")
        context = context or {}
        component_id, branch = self.SURFACES[surface]
        level = "INFO" if not self.enabled else self.provider.get_level(component_id)
        level_config = self.policy.get(branch, {}).get(level.lower()) or {}
        actions = list(level_config.get("actions", []))
        allowed, reasons = True, []
        if "hard_block" in actions:
            allowed, reasons = False, ["hard_block"]
        critical_classes = set(level_config.get("critical_classes", []))
        is_critical = context.get("critical", False) or context.get("operation_class") in critical_classes
        if allowed and "deny_non_critical" in actions and not is_critical:
            allowed, reasons = False, ["operation is non-critical"]
        if allowed and "require_approval" in actions and not context.get("approved", False):
            allowed, reasons = False, ["approval required"]
        if allowed and "require_secondary_auth" in actions and not context.get("secondary_auth", False):
            allowed, reasons = False, ["secondary authentication required"]
        configured_whitelist = (self.runtime_config.get("moscript_whitelist", [])
                                if surface == "moscript_registry" else [])
        whitelist = set(context.get("whitelist", configured_whitelist))
        runtime_id = str(context.get("runtime_id", operation))
        if allowed and ({"require_explicit_whitelist", "require_whitelist"} & set(actions)) and runtime_id not in whitelist:
            allowed, reasons = False, [f"{runtime_id} is not whitelisted"]
        if allowed and "deny_experimental" in actions and context.get("experimental", False):
            allowed, reasons = False, ["experimental operation denied"]
        if allowed and "deny_side_effects" in actions and context.get("side_effecting", False):
            allowed, reasons = False, ["side effects denied"]
        if not reasons:
            reasons = ["policy permits operation"]
        decision = RuntimeEnforcementDecision(
            f"runtime_gate_{surface}_{uuid.uuid4().hex}", surface, component_id, branch,
            operation, level, actions, allowed, "; ".join(reasons), utcnow().isoformat())
        if self.enabled:
            self.provider.audit(decision)
        return decision

    def require(self, surface: str, operation: str,
                context: Optional[Dict[str, Any]] = None) -> RuntimeEnforcementDecision:
        try:
            decision = self.evaluate(surface, operation, context)
        except Exception as exc:
            decision = RuntimeEnforcementDecision(
                f"runtime_gate_{surface}_{uuid.uuid4().hex}", surface,
                self.SURFACES.get(surface, (surface, "unknown"))[0],
                self.SURFACES.get(surface, (surface, "unknown"))[1], operation,
                "UNKNOWN", [], False,
                f"control-plane state unavailable: {type(exc).__name__}: {exc}",
                utcnow().isoformat())
        if not decision.allowed:
            raise RuntimeEnforcementDenied(decision)
        return decision


class MemoryEnforcementStateProvider:
    def __init__(self, levels: Optional[Dict[str, str]] = None):
        self.levels = {key: value.upper() for key, value in (levels or {}).items()}
        self.decisions: list[RuntimeEnforcementDecision] = []

    def get_level(self, component_id: str) -> str:
        return self.levels.get(component_id, "INFO")

    def audit(self, decision: RuntimeEnforcementDecision) -> str:
        self.decisions.append(decision)
        return f"memory-audit-{len(self.decisions)}"
