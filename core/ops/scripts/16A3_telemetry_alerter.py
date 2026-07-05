"""16A3: live telemetry aggregation and observation-only alert dispatch."""

from __future__ import annotations

import argparse
import importlib.util
import json
import logging
import os
import statistics
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

_script_dir = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("ops16a2", os.path.join(_script_dir, "16A2_telemetry_query_builder.py"))
_module = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _module
_spec.loader.exec_module(_module)
TelemetryQueryBuilder = _module.TelemetryQueryBuilder
NeonTelemetryStore = _module.NeonTelemetryStore
EventSeverity = _module.EventSeverity
utcnow = _module.utcnow

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class TelemetryEvent:
    event_type: str
    component_id: str
    severity: str
    anomaly_type: Optional[str]
    anomaly_details: Dict[str, Any]
    source_metric: str
    trace_id: str
    timestamp: datetime
    is_dry_run: bool

    def to_audit_record(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type, "component_id": self.component_id,
            "actor_id": None, "source_level": self.severity, "target_level": None,
            "policy_enforced": None,
            "event_data": {"anomaly_type": self.anomaly_type,
                           "anomaly_details": self.anomaly_details,
                           "source_metric": self.source_metric},
            "trace_id": self.trace_id, "created_at": self.timestamp,
            "created_by_component": "16A3_telemetry_alerter",
            "is_dry_run": self.is_dry_run,
        }


class SpikeDetector:
    def __init__(self, threshold_multiplier: float = 2.5, window_samples: int = 10):
        self.threshold_multiplier = threshold_multiplier
        self.window_samples = window_samples

    def detect(self, data: List[Dict[str, Any]], metric_key: str = "count") -> Tuple[bool, Optional[Dict[str, Any]]]:
        values = [float(row.get(metric_key, 0) or 0) for row in data[-self.window_samples:]]
        if len(values) < 2:
            return False, None
        baseline = statistics.mean(values[:-1])
        recent = values[-1]
        triggered = recent > 0 and (baseline == 0 or recent >= baseline * self.threshold_multiplier)
        return triggered, ({"recent_value": recent, "baseline": baseline,
                            "multiplier": recent / baseline if baseline else None} if triggered else None)


class TrendDetector:
    def __init__(self, min_samples: int = 5, trend_threshold: float = 0.1):
        self.min_samples = min_samples
        self.trend_threshold = trend_threshold

    def detect(self, data: List[Dict[str, Any]], metric_key: str = "count") -> Tuple[bool, Optional[Dict[str, Any]]]:
        values = [float(row.get(metric_key, 0) or 0) for row in data]
        if len(values) < self.min_samples:
            return False, None
        first, last = values[0], values[-1]
        change = (last - first) / max(abs(first), 1.0)
        return change >= self.trend_threshold, ({"percent_change": change, "samples": len(values)} if change >= self.trend_threshold else None)


class ThresholdDetector:
    def __init__(self, threshold: float):
        self.threshold = threshold

    def detect(self, data: List[Dict[str, Any]], metric_key: str = "count") -> Tuple[bool, Optional[Dict[str, Any]]]:
        if not data:
            return False, None
        value = float(data[-1].get(metric_key, 0) or 0)
        return value > self.threshold, ({"value": value, "threshold": self.threshold} if value > self.threshold else None)


class TelemetryAlerter:
    """Queries live metrics and emits audits; it never applies enforcement actions."""

    def __init__(self, query_builder: TelemetryQueryBuilder, dry_run: bool = False,
                 store: Optional[NeonTelemetryStore] = None):
        self.query_builder = query_builder
        self.dry_run = dry_run
        self.store = store or NeonTelemetryStore()
        logger.info("TelemetryAlerter initialized (dry_run=%s, live_store=neon)", dry_run)

    def _event(self, event_type: str, component_id: str, severity: str,
               anomaly_type: Optional[str], details: Dict[str, Any],
               source: str, trace_id: str) -> TelemetryEvent:
        return TelemetryEvent(event_type, component_id, severity, anomaly_type,
                              details, source, trace_id, utcnow(), self.dry_run)

    def detect_audit_anomalies(self, rows, component_id, trace_id):
        triggered, details = SpikeDetector(3.0).detect(rows)
        return [self._event("ANOMALY_SPIKE", component_id, "WARN", "spike", details or {}, "graph_audit_event", trace_id)] if triggered else []

    def detect_agent_anomalies(self, rows, component_id, trace_id):
        if not rows:
            return []
        return [self._event("ANOMALY_THRESHOLD", component_id, "ELEVATED", "failure_count",
                            {"failure_count": len(rows)}, "agent_run_log", trace_id)]

    def detect_decision_anomalies(self, rows, component_id, trace_id):
        if not rows:
            return []
        return [self._event("ANOMALY_THRESHOLD", component_id, "WARN", "decision_latency",
                            {"slow_decisions": len(rows)}, "decision_run_log", trace_id)]

    def detect_woo_anomalies(self, rows, component_id, trace_id):
        if not rows:
            return []
        return [self._event("ANOMALY_THRESHOLD", component_id, "ELEVATED", "woo_warning",
                            {"warnings": len(rows)}, "woo_interpretation_log", trace_id)]

    def compute_resonance_from_rows(self, results: Dict[str, List[Dict[str, Any]]], trace_id: str) -> Tuple[float, str, List[Dict[str, Any]]]:
        severity_by_query = {
            "audit_events_warn": "WARN", "audit_events_elevated": "ELEVATED",
            "audit_events_restricted": "RESTRICTED", "audit_events_locked": "LOCKED",
            "agent_failures": "ELEVATED", "decision_delays": "RESTRICTED",
            "moscript_errors": "ELEVATED", "woo_warnings": "ELEVATED",
        }
        now = utcnow()
        weighted = 0.0
        contributing = []
        for query_name, rows in results.items():
            severity = severity_by_query[query_name]
            weight = EventSeverity[severity].value
            for row in rows:
                created = row.get("created_at") or now
                if created.tzinfo is None:
                    created = created.replace(tzinfo=timezone.utc)
                age = max(0.0, (now - created).total_seconds())
                contribution = weight * self.query_builder.decay_factor(age)
                weighted += contribution
                contributing.append({"event_id": str(row.get("id")), "source": query_name,
                                     "severity": severity, "weight": weight,
                                     "age_seconds": age, "contribution": contribution,
                                     "timestamp": created.isoformat()})
        score = weighted / max(1, self.query_builder.window_seconds)
        thresholds = [("LOCKED", 3.0), ("RESTRICTED", 1.5), ("ELEVATED", 0.5), ("WARN", 0.2)]
        level = next((name for name, threshold in thresholds if score >= threshold), "INFO")
        logger.info("[%s] Resonance computed from %d live rows: %.6f (%s)", trace_id, len(contributing), score, level)
        return score, level, contributing

    def compute_resonance_score(self, events_by_severity: Dict[str, int], trace_id: str) -> Tuple[float, str]:
        weighted = sum(EventSeverity[name.upper()].value * count for name, count in events_by_severity.items())
        score = weighted / max(1, self.query_builder.window_seconds)
        level = "LOCKED" if score >= 3 else "RESTRICTED" if score >= 1.5 else "ELEVATED" if score >= .5 else "WARN" if score >= .2 else "INFO"
        return score, level

    def emit_resonance_event(self, component_id, score, level, trace_id):
        return self._event("RESONANCE_SCORE_UPDATED", component_id, level, None,
                           {"score": score, "level": level}, "composite", trace_id)

    def emit_events(self, events: List[TelemetryEvent]) -> Tuple[int, List[Dict[str, Any]], List[str]]:
        records = [event.to_audit_record() for event in events]
        if self.dry_run:
            logger.info("[DRY-RUN] Would emit %d audit events", len(records))
            return len(records), records, []
        ids = [self.store.insert_audit(record) for record in records]
        logger.info("Persisted %d audit events to Neon graph_audit_event", len(ids))
        return len(records), records, ids

    def run_iteration(self, component_id: str) -> Dict[str, Any]:
        trace_id = f"telemetry_alert_{component_id}_{utcnow().isoformat()}"
        results = self.store.execute_resonance_queries(self.query_builder)
        alerts: List[TelemetryEvent] = []
        audit_rows = (results["audit_events_warn"] + results["audit_events_elevated"] +
                      results["audit_events_restricted"] + results["audit_events_locked"])
        alerts += self.detect_audit_anomalies(audit_rows, component_id, trace_id)
        alerts += self.detect_agent_anomalies(results["agent_failures"], component_id, trace_id)
        alerts += self.detect_decision_anomalies(results["decision_delays"], component_id, trace_id)
        alerts += self.detect_woo_anomalies(results["woo_warnings"], component_id, trace_id)
        score, level, contributing = self.compute_resonance_from_rows(results, trace_id)
        alerts.append(self.emit_resonance_event(component_id, score, level, trace_id))
        count, records, audit_ids = self.emit_events(alerts)
        if not self.dry_run:
            self.store.update_score_preserving_level(component_id, score, contributing)
        return {"trace_id": trace_id, "component_id": component_id,
                "alerts_raised": count, "anomalies_detected": count - 1,
                "resonance_score": score, "resonance_level": level,
                "metric_sources": {name: len(rows) for name, rows in results.items()},
                "queries_executed": len(results), "dry_run": self.dry_run,
                "timestamp": utcnow().isoformat(), "audit_records": records,
                "audit_event_ids": audit_ids}


def main() -> None:
    parser = argparse.ArgumentParser(description="16A3 live telemetry alerter")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--component", default="system")
    args = parser.parse_args()
    result = TelemetryAlerter(TelemetryQueryBuilder(), args.dry_run).run_iteration(args.component)
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
