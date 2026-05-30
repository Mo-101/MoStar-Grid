"""Read-only dashboard telemetry for the local cluster."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from federation import AttestationLog, DisputeLog
from grid.config import CLUSTER_DIR, EVIDENCE_DIR, PROVENANCE_PATH


class ClusterTelemetry:
    def __init__(self, cluster_dir: Path | None = None, evidence_dir: Path | None = None):
        self.cluster_dir = cluster_dir or CLUSTER_DIR
        self.evidence_dir = evidence_dir or EVIDENCE_DIR
        self.attestations = AttestationLog(self.cluster_dir)
        self.disputes = DisputeLog(self.cluster_dir)

    def snapshot(
        self,
        *,
        status: dict[str, Any],
        proposals: list[dict[str, Any]],
        provenance: list[dict[str, Any]],
    ) -> dict[str, Any]:
        given = self.attestations.read_given()
        received = self.attestations.read_received()
        disputed_scrolls = self.attestations.read_disputed()
        disputes = self.disputes.read_disputes_received()
        evidence_manifests = self._read_evidence_manifests()
        active_disputes = [d for d in disputes if _is_active(d)]
        expired_disputes = [d for d in disputes if _is_expired(d)]

        return {
            "graph": status.get("mindgraph", {}),
            "density": status.get("density", {}),
            "queue": status.get("queue", {}),
            "dcx": status.get("dcx", {}),
            "scrolls": {
                "received_count": len(received),
                "given_count": len(given),
                "disputed_count": len(disputed_scrolls),
                "recent": [_scroll_summary(r) for r in _latest(received, 12)],
            },
            "attestations": {
                "given_count": len(given),
                "received_count": len(received),
                "disputed_count": len(disputed_scrolls),
                "recent_given": [_attestation_summary(r) for r in _latest(given, 8)],
                "recent_received": [_attestation_summary(r) for r in _latest(received, 8)],
                "recent_disputed": [_attestation_summary(r) for r in _latest(disputed_scrolls, 8)],
            },
            "disputes": {
                "received_count": len(disputes),
                "active_count": len(active_disputes),
                "expired_count": len(expired_disputes),
                "by_severity": _count_by(disputes, "severity"),
                "recent": [_dispute_summary(d) for d in _latest(disputes, 12, "registered_at")],
            },
            "evidence": {
                "manifest_count": len(evidence_manifests),
                "reference_count": sum(item["reference_count"] for item in evidence_manifests),
                "pending_requests": [
                    {
                        "dispute_id": d.get("dispute_id"),
                        "scroll_id": d.get("scroll_id"),
                        "disputing_cluster_id": d.get("disputing_cluster_id"),
                        "severity": d.get("severity"),
                        "expires_at": d.get("expires_at"),
                        "evidence_available": any(m["scroll_id"] == d.get("scroll_id") for m in evidence_manifests),
                    }
                    for d in active_disputes
                ],
                "manifests": evidence_manifests[:12],
            },
            "gates": {
                "latest_proposal": _proposal_gate_summary(proposals[0]) if proposals else None,
                "recent_proposal_scores": [
                    _proposal_gate_summary(proposal)
                    for proposal in proposals[:8]
                ],
                "recent_scroll_gate_receipts": [
                    _scroll_gate_summary(record)
                    for record in _latest(received, 8)
                    if _scroll_gate_summary(record)["receipts"]
                ],
            },
            "proposals": proposals,
            "provenance": {
                "recent": self._read_provenance(provenance),
            },
            "summary": {
                "graph_nodes": status.get("mindgraph", {}).get("nodes", 0),
                "graph_relationships": status.get("mindgraph", {}).get("relationships", 0),
                "pending_proposals": status.get("queue", {}).get("pending", 0),
                "received_scrolls": len(received),
                "received_attestations": len(received),
                "active_disputes": len(active_disputes),
                "evidence_manifests": len(evidence_manifests),
                "dcx_connected": bool(status.get("dcx", {}).get("connected")),
            },
        }

    def _read_evidence_manifests(self) -> list[dict[str, Any]]:
        if not self.evidence_dir.exists():
            return []
        manifests = []
        for path in sorted(self.evidence_dir.glob("*/manifest.json"), reverse=True):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            evidence = payload.get("evidence") or []
            manifests.append({
                "scroll_id": payload.get("scroll_id") or path.parent.name,
                "reference_count": len(evidence),
                "evidence": evidence,
            })
        return manifests

    def _read_provenance(self, in_memory: list[dict[str, Any]]) -> list[dict[str, Any]]:
        path = self.cluster_dir / "provenance" / "events.jsonl"
        if not path.exists():
            path = PROVENANCE_PATH
        records: list[dict[str, Any]] = []
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as handle:
                    records = [json.loads(line) for line in handle if line.strip()]
            except (OSError, json.JSONDecodeError):
                records = []
        return _latest(records, 20, "timestamp") or in_memory


def _latest(records: list[dict[str, Any]], limit: int, timestamp_key: str = "timestamp") -> list[dict[str, Any]]:
    return sorted(records, key=lambda r: str(r.get(timestamp_key, "")), reverse=True)[:limit]


def _count_by(records: list[dict[str, Any]], field: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for record in records:
        value = str(record.get(field) or "unknown")
        counts[value] = counts.get(value, 0) + 1
    return counts


def _attestation_summary(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "timestamp": record.get("timestamp"),
        "scroll_id": record.get("scroll_id"),
        "direction": record.get("direction"),
        "status": record.get("status"),
        "peer_cluster_id": record.get("cluster_attesting") or record.get("cluster_receiving") or record.get("peer_cluster_id"),
        "scroll_hash": record.get("scroll_hash"),
    }


def _scroll_summary(record: dict[str, Any]) -> dict[str, Any]:
    scroll = record.get("scroll") or {}
    action = scroll.get("action") or {}
    lifecycle = scroll.get("lifecycle") or {}
    evidence = scroll.get("evidence") or {}
    return {
        **_attestation_summary(record),
        "source_cluster_id": (scroll.get("cluster") or {}).get("cluster_id") or record.get("cluster_attesting"),
        "action_type": action.get("action_type"),
        "risk_level": action.get("risk_level"),
        "lifecycle_status": lifecycle.get("status"),
        "evidence_hash_count": len(evidence.get("evidence_hashes") or []),
        "summary": (scroll.get("human_context") or {}).get("summary"),
    }


def _dispute_summary(dispute: dict[str, Any]) -> dict[str, Any]:
    return {
        "dispute_id": dispute.get("dispute_id"),
        "scroll_id": dispute.get("scroll_id"),
        "disputing_cluster_id": dispute.get("disputing_cluster_id"),
        "reason": dispute.get("reason"),
        "severity": dispute.get("severity"),
        "status": dispute.get("status"),
        "registered_at": dispute.get("registered_at"),
        "expires_at": dispute.get("expires_at"),
        "active": _is_active(dispute),
    }


def _proposal_gate_summary(proposal: dict[str, Any]) -> dict[str, Any]:
    consistency = proposal.get("consistency") or {}
    return {
        "proposal_id": proposal.get("proposal_id"),
        "state": proposal.get("state"),
        "passed": bool(consistency.get("passed")),
        "scores": consistency.get("scores") or {},
        "thresholds": consistency.get("thresholds") or {},
        "failures": consistency.get("failures") or [],
        "proposed_at": proposal.get("proposed_at"),
    }


def _scroll_gate_summary(record: dict[str, Any]) -> dict[str, Any]:
    scroll = record.get("scroll") or {}
    return {
        "scroll_id": record.get("scroll_id"),
        "source_cluster_id": (scroll.get("cluster") or {}).get("cluster_id") or record.get("cluster_attesting"),
        "receipts": scroll.get("gate_receipts") or {},
    }


def _is_active(dispute: dict[str, Any]) -> bool:
    return dispute.get("status") == "active" and not _is_expired(dispute)


def _is_expired(dispute: dict[str, Any]) -> bool:
    expires_at = dispute.get("expires_at")
    if not expires_at:
        return False
    try:
        expires = datetime.fromisoformat(str(expires_at).replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return False
    return expires <= datetime.now(timezone.utc)
