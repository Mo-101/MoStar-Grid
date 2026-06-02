import json

from fastapi.testclient import TestClient
import pytest

from federation import (
    AttestationLog,
    Scroll,
    ScrollAction,
    ScrollEvidence,
    ScrollImporter,
    ScrollImportError,
    ScrollParticipants,
    blake3_hex,
    generate_ed25519_keypair,
)
from grid.api import app
from grid.config import MOSTAR_CLUSTER_ID


def _remote_scroll_keypair_scroll(
    *,
    cluster_id: str = "kampala-beta",
    evidence: str = "proof",
) -> tuple[Scroll, str]:
    private_key, public_key = generate_ed25519_keypair()
    scroll = Scroll.create(
        cluster_pubkey=public_key,
        cluster_id=cluster_id,
        cluster_region="east-africa",
        action=ScrollAction(action_type="supply_transfer", intent="cholera_response"),
        participants=ScrollParticipants(requester_soulprint_hash=blake3_hex("requester")),
        inputs={"clinic_id": "clinic-784", "quantity": 200},
        gate_receipts={"woo": {"status": "passed"}},
        evidence=ScrollEvidence(evidence_hashes=[blake3_hex(evidence)]),
        human_context={"summary": "Remote sealed scroll."},
        created_at="2026-05-27T14:32:25Z",
    ).seal_with_cluster_key(private_key)
    return scroll, private_key


def _remote_scroll(*, cluster_id: str = "kampala-beta", evidence: str = "proof") -> Scroll:
    return _remote_scroll_keypair_scroll(cluster_id=cluster_id, evidence=evidence)[0]


def test_import_scroll_records_received_attestation(tmp_path):
    log = AttestationLog(tmp_path / MOSTAR_CLUSTER_ID)
    scroll = _remote_scroll()

    result = ScrollImporter(log).import_scroll(scroll.to_dict())

    assert result.status == "imported"
    assert result.ready_for_attestation is True
    assert result.source_cluster_id == "kampala-beta"
    received = log.read_received()
    assert received[0]["cluster_attesting"] == "kampala-beta"
    assert received[0]["scroll_id"] == scroll.scroll_id
    assert received[0]["scroll"]["scroll_id"] == scroll.scroll_id


def test_import_scroll_rejects_tampered_payload(tmp_path):
    scroll = _remote_scroll()
    payload = scroll.to_dict()
    payload["inputs"]["quantity"] = 201

    with pytest.raises(ScrollImportError, match="invalid_scroll_signature"):
        ScrollImporter(AttestationLog(tmp_path / MOSTAR_CLUSTER_ID)).import_scroll(payload)


def test_import_scroll_rejects_invalid_evidence_hash(tmp_path):
    scroll, private_key = _remote_scroll_keypair_scroll()
    scroll.evidence.evidence_hashes = ["not-a-blake3-hash"]
    payload = scroll.seal_with_cluster_key(private_key).to_dict()

    with pytest.raises(ScrollImportError, match="invalid_evidence_hash"):
        ScrollImporter(AttestationLog(tmp_path / MOSTAR_CLUSTER_ID)).import_scroll(payload)


def test_import_scroll_verifies_supplied_evidence_blobs(tmp_path):
    scroll = _remote_scroll(evidence="proof")

    result = ScrollImporter(AttestationLog(tmp_path / MOSTAR_CLUSTER_ID)).import_scroll(
        scroll.to_dict(),
        evidence_blobs={"proof.txt": "proof"},
    )

    assert result.ready_for_attestation is True


def test_import_scroll_rejects_evidence_blob_mismatch(tmp_path):
    scroll = _remote_scroll(evidence="proof")

    with pytest.raises(ScrollImportError, match="evidence_hash_mismatch"):
        ScrollImporter(AttestationLog(tmp_path / MOSTAR_CLUSTER_ID)).import_scroll(
            scroll.to_dict(),
            evidence_blobs={"proof.txt": "wrong"},
        )


def test_import_scroll_rejects_local_cluster_scroll(tmp_path):
    scroll = _remote_scroll(cluster_id=MOSTAR_CLUSTER_ID)

    with pytest.raises(ScrollImportError, match="cannot_import_local_cluster_scroll"):
        ScrollImporter(AttestationLog(tmp_path / MOSTAR_CLUSTER_ID)).import_scroll(scroll.to_dict())


def test_api_scroll_import_returns_attestation_ready_response():
    client = TestClient(app)
    scroll = _remote_scroll()

    response = client.post("/api/scrolls/import", json={"scroll": scroll.to_dict()})

    assert response.status_code == 200
    payload = response.json()
    assert payload["cluster_id"] == MOSTAR_CLUSTER_ID
    assert payload["source_cluster_id"] == "kampala-beta"
    assert payload["scroll_id"] == scroll.scroll_id
    assert payload["status"] == "imported"
    assert payload["ready_for_attestation"] is True
    assert payload["next_step"] == "cluster_b_can_now_sign_and_attest"


def test_api_scroll_import_rejects_bad_scroll():
    client = TestClient(app)

    response = client.post("/api/scrolls/import", json={"scroll": {"bad": "payload"}})

    assert response.status_code == 422
    assert response.json()["cluster_id"] == MOSTAR_CLUSTER_ID


def test_received_attestation_jsonl_contains_imported_scroll(tmp_path):
    log = AttestationLog(tmp_path / MOSTAR_CLUSTER_ID)
    scroll = _remote_scroll()

    ScrollImporter(log).import_scroll(scroll.to_dict())
    line = log.received_path.read_text(encoding="utf-8").strip()

    payload = json.loads(line)
    assert payload["scroll_hash"] == scroll.seal.seal_hash
    assert payload["status"] == "accepted"
    assert payload["scroll"]["scroll_id"] == scroll.scroll_id


def test_cross_cluster_import_via_api_lands_in_received_jsonl(tmp_path, monkeypatch):
    log = AttestationLog(tmp_path / "clusters" / MOSTAR_CLUSTER_ID)
    monkeypatch.setattr("grid.api.ScrollImporter", lambda: ScrollImporter(log))
    cluster_a_scroll = _remote_scroll(cluster_id="kampala-beta")
    cluster_b_api = TestClient(app)

    response = cluster_b_api.post("/api/scrolls/import", json={"scroll": cluster_a_scroll.to_dict()})

    assert response.status_code == 200
    assert response.json()["ready_for_attestation"] is True
    received = log.read_received()
    assert len(received) == 1
    assert received[0]["cluster_id"] == MOSTAR_CLUSTER_ID
    assert received[0]["cluster_attesting"] == "kampala-beta"
    assert received[0]["scroll_id"] == cluster_a_scroll.scroll_id
    assert received[0]["scroll_hash"] == cluster_a_scroll.seal.seal_hash
    assert received[0]["signature"] == cluster_a_scroll.seal.cluster_signatures[0]
    assert received[0]["status"] == "accepted"
    assert received[0]["scroll"]["scroll_id"] == cluster_a_scroll.scroll_id


def test_tampered_scroll_rejected_and_not_recorded(tmp_path, monkeypatch):
    log = AttestationLog(tmp_path / "clusters" / MOSTAR_CLUSTER_ID)
    monkeypatch.setattr("grid.api.ScrollImporter", lambda: ScrollImporter(log))
    payload = _remote_scroll(cluster_id="kampala-beta").to_dict()
    payload["human_context"]["summary"] = "tampered in transit"
    cluster_b_api = TestClient(app)

    response = cluster_b_api.post("/api/scrolls/import", json={"scroll": payload})

    assert response.status_code == 422
    assert "invalid_scroll_signature" in response.json()["detail"]
    assert log.read_received() == []
    assert not log.received_path.exists()
