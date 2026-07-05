"""16A5: live Neon/Aura operational-hardening verifier aligned to 16A1."""

from __future__ import annotations

import argparse
import importlib.util
import json
import logging
import os
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List

SCRIPT_DIR = Path(__file__).resolve().parent


def load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPT_DIR / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


qb = load("ops16a2_verify", "16A2_telemetry_query_builder.py")
alerting = load("ops16a3_verify", "16A3_telemetry_alerter.py")
control = load("ops16a4_verify", "16A4_control_plane_stabilizer.py")

TelemetryQueryBuilder = qb.TelemetryQueryBuilder
NeonTelemetryStore = qb.NeonTelemetryStore
TelemetryAlerter = alerting.TelemetryAlerter
SpikeDetector = alerting.SpikeDetector
PolicyEngine = control.PolicyEngine
ThroneLockResolver = control.ThroneLockResolver
ControlPlaneStabilizer = control.ControlPlaneStabilizer
EnforcementLevel = control.EnforcementLevel
load_policy_document = control.load_policy_document
utcnow = qb.utcnow

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class CheckResult:
    check_id: str
    check_name: str
    passed: bool
    details: str
    errors: List[str]
    warnings: List[str]
    timestamp: datetime

    def to_dict(self) -> Dict[str, Any]:
        return {"check_id": self.check_id, "check_name": self.check_name,
                "passed": self.passed, "details": self.details,
                "errors": self.errors, "warnings": self.warnings,
                "timestamp": self.timestamp.isoformat()}


class OperationalHardeningVerifier:
    """Five closure checks. Live mode is required for a closable result."""

    def __init__(self, dry_run_mode: bool = True, cleanup: bool = True):
        self.live = not dry_run_mode
        self.cleanup = cleanup
        self.prefix = f"16a5_verify_{uuid.uuid4().hex[:10]}"
        self.store = NeonTelemetryStore()
        self.store.ensure_runtime_schema()
        self.builder = TelemetryQueryBuilder()
        self.document = load_policy_document()
        self.policy = PolicyEngine(self.document["policies"], self.document.get("thresholds"), self.document["_policy_path"])
        self.evidence: Dict[str, Any] = {"prefix": self.prefix}
        logger.info("OperationalHardeningVerifier initialized (live=%s, prefix=%s)", self.live, self.prefix)

    def _result(self, check_id: str, name: str, errors: List[str], details: str,
                warnings: List[str] | None = None) -> CheckResult:
        return CheckResult(check_id, name, not errors, details, errors, warnings or [], utcnow())

    def _resolver(self, dry_run: bool = False) -> ThroneLockResolver:
        return ThroneLockResolver("neo4j", self.store, self.document, dry_run)

    def _stabilizer(self, dry_run: bool = False) -> ControlPlaneStabilizer:
        resolver = self._resolver(dry_run)
        return ControlPlaneStabilizer(self.builder, self.policy, resolver, dry_run, self.store)

    def check_metric_aggregation_and_alert_dispatch(self) -> CheckResult:
        errors, warnings = [], []
        name = "Metric Aggregation and Alert Dispatch"
        try:
            connection = self.store.verify_connectivity()
            results = self.store.execute_resonance_queries(self.builder)
            expected = set(self.builder.query_resonance_components())
            if set(results) != expected:
                errors.append(f"Executed query set differs: {set(results) ^ expected}")
            sources = {query.source.name for query in self.builder.query_resonance_components().values()}
            required_sources = {source.name for source in qb.MetricSource}
            if sources != required_sources:
                errors.append(f"Metric source coverage differs: missing={required_sources - sources}")
            triggered, _ = SpikeDetector(2.5).detect([{"count": 1}, {"count": 1}, {"count": 10}])
            if not triggered:
                errors.append("Known spike pattern did not trigger anomaly detector")
            component = f"{self.prefix}_metrics"
            alerter = TelemetryAlerter(self.builder, dry_run=not self.live, store=self.store)
            iteration = alerter.run_iteration(component)
            if iteration["queries_executed"] != 8:
                errors.append(f"Expected 8 live queries, got {iteration['queries_executed']}")
            if self.live:
                persisted = self.store.get_audits(trace_id=iteration["trace_id"])
                if len(persisted) != iteration["alerts_raised"]:
                    errors.append(f"Alert dispatch mismatch: emitted={iteration['alerts_raised']} persisted={len(persisted)}")
            else:
                warnings.append("Non-live verifier run cannot prove persisted alert dispatch")
                errors.append("CHK_001 requires --live")
            self.evidence["chk_001"] = {"connection": connection,
                                         "row_counts": {key: len(value) for key, value in results.items()},
                                         "trace_id": iteration["trace_id"],
                                         "audit_event_ids": iteration["audit_event_ids"]}
            details = f"Executed 8 parameterized queries across 5 Neon sources; persisted {len(iteration['audit_event_ids'])} alert audits"
        except Exception as exc:
            errors.append(f"{type(exc).__name__}: {exc}")
            details = "Live metric aggregation or alert dispatch failed"
            logger.exception("CHK_001 failed")
        return self._result("CHK_001", name, errors, details, warnings)

    def check_policy_application_and_thronelock(self) -> CheckResult:
        errors, warnings = [], []
        name = "Policy Application and ThroneLock Precedence"
        try:
            if Path(self.policy.policy_path).resolve() != Path(control.DEFAULT_POLICY_FILE).resolve():
                errors.append(f"Unexpected policy path: {self.policy.policy_path}")
            component = f"{self.prefix}_policy"
            self.store.upsert_state(component, 3.2, "INFO", [], "verifier_seed")
            stabilizer = self._stabilizer(dry_run=not self.live)
            result = stabilizer.run_iteration(component, "agent_execution")
            resolution = result["thronelock_resolution"]
            if resolution["source_used"] != "neo4j":
                errors.append(f"Aura primary was not used: {resolution}")
            if resolution["fallback_reason"] is not None:
                errors.append(f"Unexpected Aura fallback: {resolution['fallback_reason']}")
            expected_level = "RESTRICTED" if "ThroneLock override" in result["reasoning"] else "LOCKED"
            if result["new_level"] != expected_level:
                errors.append(f"Expected {expected_level}, got {result['new_level']}")
            required_action = "hard_block" if expected_level == "LOCKED" else "deny_non_critical"
            if required_action not in result["actions_applied"]:
                errors.append(f"Missing required {expected_level} action: {required_action}")
            if not self.live:
                errors.append("CHK_002 requires --live")
            elif not result.get("audit_event_id") or not resolution.get("audit_event_id"):
                errors.append("Policy or ThroneLock source decision was not persisted")
            self.evidence["chk_002"] = {"policy_path": self.policy.policy_path,
                                         "trace_id": result["trace_id"],
                                         "new_level": result["new_level"],
                                         "actions": result["actions_applied"],
                                         "thronelock_resolution": resolution,
                                         "audit_event_id": result.get("audit_event_id")}
            details = f"Loaded real YAML policy; applied {result['new_level']} via Aura source={resolution['source_used']}"
        except Exception as exc:
            errors.append(f"{type(exc).__name__}: {exc}")
            details = "Live policy application or ThroneLock resolution failed"
            logger.exception("CHK_002 failed")
        return self._result("CHK_002", name, errors, details, warnings)

    def check_persisted_audit_completeness(self) -> CheckResult:
        errors, warnings = [], []
        name = "Persisted Audit Trail Completeness"
        try:
            traces = [self.evidence.get("chk_001", {}).get("trace_id"),
                      self.evidence.get("chk_002", {}).get("trace_id")]
            records = [record for trace in traces if trace for record in self.store.get_audits(trace_id=trace)]
            if not records:
                errors.append("No persisted audit records found for prior live checks")
            required_payload = {"event_type", "component_id", "source_level", "trace_id", "created_by_component", "is_dry_run"}
            for record in records:
                payload = record.get("payload_json") or {}
                missing = required_payload - set(payload)
                if missing:
                    errors.append(f"Audit {record['id']} missing payload fields {sorted(missing)}")
                if payload.get("is_dry_run"):
                    errors.append(f"Live audit {record['id']} marked dry-run")
            types = {record["event_type"] for record in records}
            if "RESONANCE_SCORE_UPDATED" not in types:
                errors.append("No persisted resonance audit from CHK_001")
            if not (types & {"CONTROL_PLANE_LOCKED", "CONTROL_PLANE_RESTRICTED"}):
                errors.append("No persisted enforcement audit from CHK_002")
            self.evidence["chk_003"] = {"audit_count": len(records),
                                         "audit_ids": [str(record["id"]) for record in records],
                                         "event_types": sorted(types)}
            details = f"Read back {len(records)} Neon audits with trace, source, level, and dry-run fields"
        except Exception as exc:
            errors.append(f"{type(exc).__name__}: {exc}")
            details = "Persisted audit validation failed"
            logger.exception("CHK_003 failed")
        return self._result("CHK_003", name, errors, details, warnings)

    def check_dry_run_noop(self) -> CheckResult:
        errors, warnings = [], []
        name = "Dry-Run No-Op Safety"
        try:
            component = f"{self.prefix}_dryrun"
            before_audits = self.store.get_audits(component_id=component)
            before_state = self.store.get_state(component)
            alert_result = TelemetryAlerter(self.builder, True, self.store).run_iteration(component)
            control_result = self._stabilizer(True).run_iteration(component, "agent_execution")
            after_audits = self.store.get_audits(component_id=component)
            after_state = self.store.get_state(component)
            if before_audits != after_audits:
                errors.append("Dry-run changed graph_audit_event")
            if before_state != after_state:
                errors.append("Dry-run changed control_plane_resonance_state")
            if alert_result.get("audit_event_ids"):
                errors.append("Dry-run alerter returned persisted audit IDs")
            if control_result.get("audit_event_id"):
                errors.append("Dry-run stabilizer returned a persisted audit ID")
            self.evidence["chk_004"] = {"alerter_trace_id": alert_result["trace_id"],
                                         "stabilizer_trace_id": control_result["trace_id"],
                                         "audit_rows_before": len(before_audits),
                                         "audit_rows_after": len(after_audits),
                                         "state_before": before_state, "state_after": after_state}
            details = "Compared Neon audit/state snapshots before and after both dry-run paths; no changes"
        except Exception as exc:
            errors.append(f"{type(exc).__name__}: {exc}")
            details = "Dry-run no-op validation failed"
            logger.exception("CHK_004 failed")
        return self._result("CHK_004", name, errors, details, warnings)

    def check_recovery_and_deescalation(self) -> CheckResult:
        errors, warnings = [], []
        name = "Recovery and De-escalation"
        transitions = []
        try:
            component = f"{self.prefix}_recovery"
            cases = [("LOCKED", 2.0, "RESTRICTED"),
                     ("RESTRICTED", 1.0, "ELEVATED"),
                     ("ELEVATED", .30, "WARN"),
                     ("WARN", .10, "INFO")]
            for old, score, expected in cases:
                self.store.upsert_state(component, score, old, [], "verifier_recovery_seed")
                result = self._stabilizer(dry_run=not self.live).run_iteration(component, "agent_execution")
                if result["new_level"] != expected:
                    errors.append(f"{old} recovery expected {expected}, got {result['new_level']}")
                if not result.get("recovery_reason"):
                    errors.append(f"{old}->{expected} has no logged recovery reason")
                if self.live:
                    audits = self.store.get_audits(trace_id=result["trace_id"])
                    if not any(record["event_type"] == "CONTROL_PLANE_RELAXED" for record in audits):
                        errors.append(f"{old}->{expected} recovery audit was not persisted")
                transitions.append({"old": old, "score": score, "new": result["new_level"],
                                    "trace_id": result["trace_id"], "audit_event_id": result.get("audit_event_id")})
            self.store.upsert_state(component, 4.0, "LOCKED", [], "verifier_manual_reset_seed")
            reset = self._stabilizer(dry_run=not self.live).manual_reset(component, "16A5 verifier reset", "16A5")
            if reset["new_level"] != "INFO":
                errors.append("Manual reset did not return to INFO")
            if self.live:
                reset_audits = self.store.get_audits(trace_id=reset["trace_id"])
                if not any(record["event_type"] == "RESONANCE_MANUAL_RESET" for record in reset_audits):
                    errors.append("Manual reset audit was not persisted")
            else:
                errors.append("CHK_005 requires --live")
            self.evidence["chk_005"] = {"transitions": transitions, "manual_reset": reset}
            details = "Persisted each one-step recovery LOCKED->RESTRICTED->ELEVATED->WARN->INFO and audited manual reset"
        except Exception as exc:
            errors.append(f"{type(exc).__name__}: {exc}")
            details = "Live recovery/de-escalation validation failed"
            logger.exception("CHK_005 failed")
        return self._result("CHK_005", name, errors, details, warnings)

    # Backward-compatible method names used by earlier runners.
    check_alerter_signal_integrity = check_metric_aggregation_and_alert_dispatch
    check_enforcer_policy_application = check_policy_application_and_thronelock
    check_audit_trail_completeness = check_persisted_audit_completeness
    check_dry_run_safety = check_dry_run_noop

    def run_all_checks(self) -> Dict[str, Any]:
        checks: List[Callable[[], CheckResult]] = [
            self.check_metric_aggregation_and_alert_dispatch,
            self.check_policy_application_and_thronelock,
            self.check_persisted_audit_completeness,
            self.check_dry_run_noop,
            self.check_recovery_and_deescalation,
        ]
        results = []
        try:
            for check in checks:
                result = check()
                results.append(result)
                logger.info("%s %s: %s", "PASS" if result.passed else "FAIL", result.check_id, result.check_name)
                for error in result.errors:
                    logger.error("  %s", error)
        finally:
            if self.cleanup:
                self.store.cleanup_verifier_records(self.prefix)
        passed = sum(result.passed for result in results)
        return {"overall_passed": passed == len(checks) and self.live,
                "mode": "live" if self.live else "dry-run-only",
                "checks_passed": passed, "checks_total": len(checks),
                "results": [result.to_dict() for result in results],
                "integration_evidence": self.evidence,
                "cleanup_performed": self.cleanup,
                "timestamp": utcnow().isoformat()}


def main() -> None:
    parser = argparse.ArgumentParser(description="16A5 live operational-hardening verifier")
    parser.add_argument("--live", action="store_true", help="Exercise Neon writes and Aura primary resolution")
    parser.add_argument("--keep-evidence", action="store_true", help="Retain isolated verifier rows")
    parser.add_argument("--output", choices=["text", "json"], default="text")
    args = parser.parse_args()
    verifier = OperationalHardeningVerifier(dry_run_mode=not args.live, cleanup=not args.keep_evidence)
    results = verifier.run_all_checks()
    if args.output == "json":
        print(json.dumps(results, indent=2, default=str))
    else:
        for result in results["results"]:
            print(f"{'PASS' if result['passed'] else 'FAIL'} {result['check_id']}: {result['check_name']} - {result['details']}")
        print(f"Overall: {'PASS' if results['overall_passed'] else 'FAIL'} ({results['checks_passed']}/{results['checks_total']}, mode={results['mode']})")
    raise SystemExit(0 if results["overall_passed"] else 1)


if __name__ == "__main__":
    main()
