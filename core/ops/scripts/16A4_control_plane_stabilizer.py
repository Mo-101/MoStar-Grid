"""16A4: policy-driven control-plane state, ThroneLock resolution, and recovery."""

from __future__ import annotations

import argparse
import importlib.util
import json
import logging
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import IntEnum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml
from dotenv import load_dotenv

_script_dir = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("ops16a2", os.path.join(_script_dir, "16A2_telemetry_query_builder.py"))
_module = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _module
_spec.loader.exec_module(_module)
TelemetryQueryBuilder = _module.TelemetryQueryBuilder
NeonTelemetryStore = _module.NeonTelemetryStore
utcnow = _module.utcnow

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_POLICY_FILE = ROOT / "core" / "ops" / "config" / "enforcement_policy.yaml"
load_dotenv(ROOT / ".env")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)


class EnforcementLevel(IntEnum):
    INFO = 0
    WARN = 1
    ELEVATED = 2
    RESTRICTED = 3
    LOCKED = 4

    @classmethod
    def from_string(cls, value: str) -> "EnforcementLevel":
        return cls[str(value).upper()]

    def lower(self) -> Optional["EnforcementLevel"]:
        return EnforcementLevel(self.value - 1) if self.value > 0 else None


@dataclass
class ControlDecision:
    decision_id: str
    component_id: str
    actor_id: str
    old_level: EnforcementLevel
    new_level: EnforcementLevel
    policy_enforced: str
    actions_applied: List[str]
    thronelock_override: bool
    reasoning: str
    timestamp: datetime
    is_dry_run: bool
    thronelock_source: str = "unknown"
    recovery_reason: Optional[str] = None

    def to_audit_record(self) -> Dict[str, Any]:
        if self.new_level < self.old_level:
            event_type = "CONTROL_PLANE_RELAXED"
        elif self.new_level == EnforcementLevel.LOCKED and self.new_level != self.old_level:
            event_type = "CONTROL_PLANE_LOCKED"
        elif self.new_level == EnforcementLevel.RESTRICTED and self.new_level != self.old_level:
            event_type = "CONTROL_PLANE_RESTRICTED"
        elif self.new_level != self.old_level:
            event_type = "CONTROL_PLANE_LEVEL_TRANSITION"
        else:
            event_type = "CONTROL_PLANE_ENFORCED"
        return {
            "event_type": event_type, "component_id": self.component_id,
            "actor_id": self.actor_id, "source_level": self.old_level.name,
            "target_level": self.new_level.name, "policy_enforced": self.policy_enforced,
            "event_data": {"actions_applied": self.actions_applied,
                           "thronelock_override": self.thronelock_override,
                           "thronelock_source": self.thronelock_source,
                           "reasoning": self.reasoning,
                           "recovery_reason": self.recovery_reason},
            "trace_id": self.decision_id, "created_at": self.timestamp,
            "created_by_component": "16A4_control_plane_stabilizer",
            "is_dry_run": self.is_dry_run,
        }


def load_policy_document(policy_file: os.PathLike[str] | str = DEFAULT_POLICY_FILE) -> Dict[str, Any]:
    path = Path(policy_file)
    if not path.is_file():
        raise FileNotFoundError(f"16A policy file not found: {path}")
    with path.open(encoding="utf-8") as handle:
        document = yaml.safe_load(handle) or {}
    if not isinstance(document.get("policies"), dict):
        raise ValueError(f"16A policy has no policies mapping: {path}")
    document["_policy_path"] = str(path.resolve())
    return document


def load_policy_from_file(policy_file: os.PathLike[str] | str) -> Dict[str, Any]:
    return load_policy_document(policy_file)["policies"]


class PolicyEngine:
    """Loads only explicit policy actions and owns threshold/hysteresis rules."""

    def __init__(self, policy_dict: Optional[Dict[str, Any]] = None,
                 thresholds: Optional[Dict[str, Any]] = None,
                 policy_path: Optional[str] = None):
        if policy_dict is None:
            document = load_policy_document()
            policy_dict, thresholds = document["policies"], document.get("thresholds", {})
            policy_path = document["_policy_path"]
        self.policy = policy_dict
        self.thresholds = thresholds or {}
        self.policy_path = policy_path or "in-memory"
        self.validate()
        logger.info("PolicyEngine loaded %d branches from %s", len(self.policy), self.policy_path)

    def _default_policy(self) -> Dict[str, Any]:
        return load_policy_document()["policies"]

    def get_actions_for_level(self, component_type: str, level: EnforcementLevel) -> List[str]:
        config = self.policy.get(component_type, {}).get(level.name.lower()) or {}
        actions = config.get("actions", [])
        if not isinstance(actions, list):
            raise ValueError(f"actions must be a list: {component_type}/{level.name}")
        return list(actions)

    def is_action_permitted(self, component_type: str, action: str, level: EnforcementLevel) -> bool:
        return action in self.get_actions_for_level(component_type, level)

    def validate(self) -> None:
        required = {EnforcementLevel.INFO: set(), EnforcementLevel.WARN: set(),
                    EnforcementLevel.ELEVATED: set(),
                    EnforcementLevel.RESTRICTED: {"deny_non_critical"},
                    EnforcementLevel.LOCKED: {"hard_block"}}
        for component, branch in self.policy.items():
            missing_levels = [level.name for level in EnforcementLevel if level.name.lower() not in branch]
            if missing_levels:
                raise ValueError(f"{component} missing enforcement levels: {missing_levels}")
            if self.get_actions_for_level(component, EnforcementLevel.INFO):
                raise ValueError(f"{component}/INFO must have no enforcement actions")
            if self.get_actions_for_level(component, EnforcementLevel.WARN):
                raise ValueError(f"{component}/WARN must have no enforcement actions")
            # Every branch must have a meaningful restriction and an explicit hard stop.
            restricted = set(self.get_actions_for_level(component, EnforcementLevel.RESTRICTED))
            locked = set(self.get_actions_for_level(component, EnforcementLevel.LOCKED))
            if not (restricted & {"deny_non_critical", "require_secondary_auth",
                                  "deny_experimental", "deny_side_effects"}):
                raise ValueError(f"{component}/RESTRICTED lacks a restrictive action")
            if "hard_block" not in locked:
                raise ValueError(f"{component}/LOCKED lacks hard_block")

    def threshold(self, level: EnforcementLevel) -> float:
        if level == EnforcementLevel.INFO:
            return 0.0
        return float(self.thresholds.get(f"threshold_{level.name.lower()}",
                         {EnforcementLevel.WARN: .2, EnforcementLevel.ELEVATED: .5,
                          EnforcementLevel.RESTRICTED: 1.5, EnforcementLevel.LOCKED: 3.0}[level]))

    @property
    def hysteresis(self) -> float:
        return float(self.thresholds.get("recovery_hysteresis", .7))

    def level_for_score(self, score: float) -> EnforcementLevel:
        for level in (EnforcementLevel.LOCKED, EnforcementLevel.RESTRICTED,
                      EnforcementLevel.ELEVATED, EnforcementLevel.WARN):
            if score >= self.threshold(level):
                return level
        return EnforcementLevel.INFO


class ThroneLockResolver:
    """Resolve Aura first; fall back only when the selected source is unavailable."""

    def __init__(self, source: str = "neo4j", store: Optional[NeonTelemetryStore] = None,
                 policy_document: Optional[Dict[str, Any]] = None, dry_run: bool = False):
        self.source = source.lower()
        if self.source not in {"neo4j", "neon", "config"}:
            raise ValueError(f"Unknown ThroneLock source: {source}")
        self.store = store or NeonTelemetryStore()
        self.policy_document = policy_document or load_policy_document()
        self.dry_run = dry_run
        self.last_resolution: Dict[str, Any] = {}

    @staticmethod
    def _permissions(value: Any) -> List[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(item) for item in value]
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                return parsed if isinstance(parsed, list) else [value]
            except json.JSONDecodeError:
                return [item.strip() for item in value.split(",") if item.strip()]
        return [str(value)]

    def _resolve_from_neo4j(self, trace_id: str) -> Dict[str, Any]:
        from neo4j import GraphDatabase
        uri = os.getenv("NEO4J_URI")
        user = os.getenv("NEO4J_USERNAME") or os.getenv("NEO4J_USER")
        password = os.getenv("NEO4J_PASSWORD")
        if not all((uri, user, password)):
            raise RuntimeError("NEO4J_URI/NEO4J_USERNAME/NEO4J_PASSWORD are required")
        query = """MATCH (r)
                   WHERE any(label IN labels(r) WHERE toLower(label) = 'graph_role')
                     AND coalesce(r.is_active, false) = true
                   RETURN coalesce(r.id,r.canonical_id,r.name) AS id,
                          r.permissions AS permissions,
                          coalesce(r.enforcement_level,'INFO') AS enforcement_level,
                          r.validity_end AS validity_end"""
        database = os.getenv("NEO4J_DATABASE", "neo4j")
        with GraphDatabase.driver(uri, auth=(user, password)) as driver:
            driver.verify_connectivity()
            with driver.session(database=database) as session:
                labels = {row["label"].lower() for row in
                          session.run("CALL db.labels() YIELD label RETURN label").data()}
                if "graph_role" not in labels:
                    return {}
                rows = session.run(query).data()
        now = utcnow()
        roles = {}
        for row in rows:
            validity = row.get("validity_end")
            if validity is not None:
                try:
                    valid_dt = validity.to_native() if hasattr(validity, "to_native") else datetime.fromisoformat(str(validity))
                    if valid_dt.tzinfo is None:
                        valid_dt = valid_dt.replace(tzinfo=timezone.utc)
                    if valid_dt <= now:
                        continue
                except (TypeError, ValueError):
                    logger.warning("[%s] Ignoring unparseable role validity for %s", trace_id, row.get("id"))
                    continue
            role_id = str(row["id"])
            roles[role_id] = {"id": role_id, "permissions": self._permissions(row.get("permissions")),
                              "enforcement_level": row.get("enforcement_level", "INFO"),
                              "source": "neo4j", "resolved_at": now.isoformat()}
        return roles

    def _resolve_from_neon(self, trace_id: str) -> Dict[str, Any]:
        from psycopg.rows import dict_row
        conn = self.store._connect()
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("SELECT to_regclass('public.graph_role') AS table_name")
            if cur.fetchone()["table_name"] is None:
                return {}
            cur.execute("SELECT * FROM graph_role WHERE is_active=TRUE")
            rows = cur.fetchall()
        now = utcnow().isoformat()
        return {str(row.get("id") or row.get("canonical_id") or row.get("name")):
                {"id": str(row.get("id") or row.get("canonical_id") or row.get("name")),
                 "permissions": self._permissions(row.get("permissions")),
                 "enforcement_level": row.get("enforcement_level", "INFO"),
                 "source": "neon", "resolved_at": now} for row in rows}

    def _resolve_from_config(self, trace_id: str) -> Dict[str, Any]:
        roles = self.policy_document.get("thronelock", {}).get("bootstrap_roles", []) or []
        now = utcnow().isoformat()
        return {str(role["id"]): {**role, "source": "config", "resolved_at": now,
                                  "staleness_warning": "bootstrap/emergency fallback"} for role in roles}

    def _audit_resolution(self, trace_id: str, source_used: str, roles: Dict[str, Any],
                          fallback_reason: Optional[str]) -> Optional[str]:
        record = {"event_type": "THRONELOCK_SOURCE_RESOLVED", "component_id": "thronelock",
                  "actor_id": "system", "source_level": "INFO", "target_level": None,
                  "policy_enforced": "thronelock_precedence",
                  "event_data": {"requested_source": self.source, "source_used": source_used,
                                 "role_ids": list(roles), "fallback_reason": fallback_reason},
                  "trace_id": trace_id, "created_at": utcnow(),
                  "created_by_component": "16A4_control_plane_stabilizer",
                  "is_dry_run": self.dry_run}
        return None if self.dry_run else self.store.insert_audit(record)

    def resolve_active_roles(self, trace_id: str) -> Dict[str, Any]:
        source_used, fallback_reason = self.source, None
        try:
            roles = getattr(self, f"_resolve_from_{self.source}")(trace_id)
        except Exception as primary_error:
            if self.source == "config":
                raise
            fallback_reason = f"{type(primary_error).__name__}: {primary_error}"
            logger.warning("[%s] ThroneLock %s unavailable: %s", trace_id, self.source, fallback_reason)
            try:
                source_used = "neon" if self.source == "neo4j" else "config"
                roles = getattr(self, f"_resolve_from_{source_used}")(trace_id)
            except Exception as secondary_error:
                if source_used == "config":
                    raise
                source_used = "config"
                fallback_reason += f"; neon: {type(secondary_error).__name__}: {secondary_error}"
                roles = self._resolve_from_config(trace_id)
        audit_id = self._audit_resolution(trace_id, source_used, roles, fallback_reason)
        self.last_resolution = {"requested_source": self.source, "source_used": source_used,
                                "fallback_reason": fallback_reason, "role_count": len(roles),
                                "audit_event_id": audit_id}
        logger.info("[%s] ThroneLock resolved %d roles from %s", trace_id, len(roles), source_used)
        return roles


class ControlPlaneStabilizer:
    def __init__(self, query_builder: TelemetryQueryBuilder, policy_engine: PolicyEngine,
                 thronelock_resolver: ThroneLockResolver, dry_run: bool = False,
                 store: Optional[NeonTelemetryStore] = None):
        self.query_builder = query_builder
        self.policy_engine = policy_engine
        self.thronelock_resolver = thronelock_resolver
        self.dry_run = dry_run
        self.store = store or thronelock_resolver.store

    def get_current_resonance_state(self, component_id: str, trace_id: str) -> Tuple[float, EnforcementLevel]:
        state = self.store.get_state(component_id)
        if not state:
            return 0.0, EnforcementLevel.INFO
        return float(state["current_score"]), EnforcementLevel.from_string(state["level"])

    @staticmethod
    def _has_override(roles: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        for role_id, role in roles.items():
            permissions = {str(item).lower() for item in role.get("permissions", [])}
            if permissions & {"override_enforcement", "thronelock"}:
                return True, role_id
        return False, None

    def check_thronelock_override(self, component_id: str, trace_id: str) -> Tuple[bool, Optional[str]]:
        return self._has_override(self.thronelock_resolver.resolve_active_roles(trace_id))

    def check_recovery_conditions(self, component_id: str, current_level: EnforcementLevel,
                                  trace_id: str, current_score: Optional[float] = None) -> Optional[EnforcementLevel]:
        if current_level == EnforcementLevel.INFO:
            return None
        if current_score is None:
            current_score, _ = self.get_current_resonance_state(component_id, trace_id)
        boundary = self.policy_engine.threshold(current_level) * self.policy_engine.hysteresis
        return current_level.lower() if current_score < boundary else None

    def compute_enforcement_decision(self, component_id: str, component_type: str,
                                     current_score: float, active_roles: Dict[str, Any],
                                     trace_id: str, current_level: EnforcementLevel = EnforcementLevel.INFO
                                     ) -> Tuple[EnforcementLevel, List[str], str]:
        desired = self.policy_engine.level_for_score(current_score)
        recovery = self.check_recovery_conditions(component_id, current_level, trace_id, current_score)
        if desired < current_level:
            target = recovery if recovery is not None else current_level
            transition_reason = (f"recovery hysteresis satisfied; one-step downgrade to {target.name}"
                                 if recovery else "recovery hysteresis not yet satisfied")
        else:
            target, transition_reason = desired, "score threshold evaluation"
        override, role_id = self._has_override(active_roles)
        if override and target == EnforcementLevel.LOCKED:
            target = EnforcementLevel.RESTRICTED
            transition_reason += f"; ThroneLock override {role_id} downgraded LOCKED"
        actions = self.policy_engine.get_actions_for_level(component_type, target)
        reasoning = (f"score={current_score:.6f}; current={current_level.name}; desired={desired.name}; "
                     f"target={target.name}; {transition_reason}; actions={actions}")
        return target, actions, reasoning

    def apply_enforcement(self, decision: ControlDecision) -> Dict[str, Any]:
        record = decision.to_audit_record()
        base = {"dry_run": self.dry_run, "decision_id": decision.decision_id,
                "component_id": decision.component_id, "old_level": decision.old_level.name,
                "new_level": decision.new_level.name, "actions_applied": decision.actions_applied,
                "reasoning": decision.reasoning, "thronelock_source": decision.thronelock_source,
                "recovery_reason": decision.recovery_reason}
        if self.dry_run:
            return base | {"would_persist_to": ["graph_audit_event", "control_plane_resonance_state"]}
        audit_id = self.store.insert_audit(record)
        state = self.store.get_state(decision.component_id)
        score = float(state["current_score"]) if state else 0.0
        events = state.get("contributing_events", []) if state else []
        self.store.upsert_state(decision.component_id, score, decision.new_level.name, events,
                                decision.recovery_reason or "policy_evaluation", decision.old_level.name)
        return base | {"audit_event_id": audit_id}

    def run_iteration(self, component_id: str, component_type: str) -> Dict[str, Any]:
        trace_id = f"enforce_{component_id}_{utcnow().isoformat()}"
        score, current = self.get_current_resonance_state(component_id, trace_id)
        roles = self.thronelock_resolver.resolve_active_roles(trace_id)
        override, role_id = self._has_override(roles)
        target, actions, reasoning = self.compute_enforcement_decision(
            component_id, component_type, score, roles, trace_id, current)
        recovery_reason = None
        if target < current:
            recovery_reason = (f"score {score:.6f} below {current.name} recovery boundary "
                               f"{self.policy_engine.threshold(current) * self.policy_engine.hysteresis:.6f}")
        decision = ControlDecision(trace_id, component_id, role_id or "system", current, target,
                                   component_type, actions, override, reasoning, utcnow(), self.dry_run,
                                   self.thronelock_resolver.last_resolution.get("source_used", "unknown"),
                                   recovery_reason)
        result = self.apply_enforcement(decision)
        result["trace_id"] = trace_id
        result["thronelock_resolution"] = self.thronelock_resolver.last_resolution
        return result

    def manual_reset(self, component_id: str, reason: str, actor_id: str) -> Dict[str, Any]:
        trace_id = f"manual_reset_{component_id}_{utcnow().isoformat()}"
        score, current = self.get_current_resonance_state(component_id, trace_id)
        record = {"event_type": "RESONANCE_MANUAL_RESET", "component_id": component_id,
                  "actor_id": actor_id, "source_level": current.name, "target_level": "INFO",
                  "policy_enforced": "manual_reset", "event_data": {"reason": reason, "previous_score": score},
                  "trace_id": trace_id, "created_at": utcnow(),
                  "created_by_component": "16A4_control_plane_stabilizer", "is_dry_run": self.dry_run}
        if self.dry_run:
            return {"dry_run": True, "trace_id": trace_id, "old_level": current.name, "new_level": "INFO"}
        audit_id = self.store.insert_audit(record)
        self.store.upsert_state(component_id, 0.0, "INFO", [], reason, current.name)
        return {"dry_run": False, "trace_id": trace_id, "old_level": current.name,
                "new_level": "INFO", "audit_event_id": audit_id}


def main() -> None:
    parser = argparse.ArgumentParser(description="16A4 live control-plane stabilizer")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--component", default="system")
    parser.add_argument("--component-type", default="agent_execution")
    parser.add_argument("--policy-file", default=str(DEFAULT_POLICY_FILE))
    parser.add_argument("--thronelock-source", choices=["neo4j", "neon", "config"], default="neo4j")
    args = parser.parse_args()
    store = NeonTelemetryStore()
    store.ensure_runtime_schema()
    document = load_policy_document(args.policy_file)
    policy = PolicyEngine(document["policies"], document.get("thresholds"), document["_policy_path"])
    resolver = ThroneLockResolver(args.thronelock_source, store, document, args.dry_run)
    result = ControlPlaneStabilizer(TelemetryQueryBuilder(), policy, resolver, args.dry_run, store).run_iteration(args.component, args.component_type)
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
