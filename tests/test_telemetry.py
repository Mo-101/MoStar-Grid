import json

from fastapi.testclient import TestClient

from federation import AttestationLog, AttestationRecord
from grid.api import app
from grid.config import MOSTAR_CLUSTER_ID
from grid.telemetry import ClusterTelemetry


def test_cluster_telemetry_reads_live_cluster_files(tmp_path):
    cluster_dir = tmp_path / "clusters" / MOSTAR_CLUSTER_ID
    evidence_dir = cluster_dir / "evidence"
    log = AttestationLog(cluster_dir)
    log.record_received(
        AttestationRecord.create(
            scroll_id="scr-kampala-beta-001",
            peer_cluster_id="kampala-beta",
            signature="sig",
            scroll_hash="hash",
            status="accepted",
            direction="received",
            scroll={
                "cluster": {"cluster_id": "kampala-beta"},
                "action": {"action_type": "supply_transfer", "risk_level": "low"},
                "evidence": {"evidence_hashes": ["abc"]},
                "gate_receipts": {"woo": {"status": "passed"}},
                "human_context": {"summary": "Remote scroll"},
                "lifecycle": {"status": "sealed"},
            },
        )
    )
    dispute = {
        "dispute_id": "dsp-nairobi-alpha-001",
        "scroll_id": "scr-kampala-beta-001",
        "disputing_cluster_id": "nairobi-alpha",
        "reason": "anomaly_detected",
        "details": "Quantity anomaly",
        "severity": "high",
        "status": "active",
        "registered_at": "2026-05-27T00:00:00Z",
        "expires_at": "2999-05-27T00:00:00Z",
        "signature": "sig",
    }
    (cluster_dir / "disputes_received.jsonl").write_text(json.dumps(dispute) + "\n", encoding="utf-8")
    (evidence_dir / "scr-kampala-beta-001").mkdir(parents=True)
    (evidence_dir / "scr-kampala-beta-001" / "manifest.json").write_text(
        json.dumps({
            "scroll_id": "scr-kampala-beta-001",
            "evidence": [{"evidence_hash": "abc", "content_type": "proof"}],
        }),
        encoding="utf-8",
    )

    telemetry = ClusterTelemetry(cluster_dir=cluster_dir, evidence_dir=evidence_dir).snapshot(
        status=_status(),
        proposals=[_proposal()],
        provenance=[{"event_type": "proposal_created"}],
    )

    assert telemetry["summary"]["received_scrolls"] == 1
    assert telemetry["attestations"]["received_count"] == 1
    assert telemetry["disputes"]["active_count"] == 1
    assert telemetry["evidence"]["manifest_count"] == 1
    assert telemetry["evidence"]["pending_requests"][0]["evidence_available"] is True
    assert telemetry["gates"]["latest_proposal"]["scores"]["ikang"] == 0.9
    assert telemetry["gates"]["recent_scroll_gate_receipts"][0]["receipts"]["woo"]["status"] == "passed"


def test_api_telemetry_returns_cluster_metadata():
    response = TestClient(app).get("/api/telemetry")

    assert response.status_code == 200
    payload = response.json()
    assert payload["cluster_id"] == MOSTAR_CLUSTER_ID
    assert "summary" in payload
    assert "scrolls" in payload
    assert "attestations" in payload
    assert "disputes" in payload
    assert "evidence" in payload
    assert "gates" in payload


def _status() -> dict:
    return {
        "mindgraph": {"nodes": 18, "relationships": 17, "status": "connected"},
        "density": {"promotion_ready": False},
        "queue": {"pending": 1, "total_proposals": 1},
        "dcx": {"connected": False},
    }


def _proposal() -> dict:
    return {
        "proposal_id": "proposal-test",
        "state": "PROPOSED",
        "proposed_at": "2026-05-27T00:00:00Z",
        "consistency": {
            "passed": False,
            "scores": {"ikang": 0.9},
            "thresholds": {"ikang": 0.75},
            "failures": ["mmong"],
        },
    }
