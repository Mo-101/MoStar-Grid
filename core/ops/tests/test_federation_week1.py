import json
from pathlib import Path

import pytest

from federation import (
    AttestationLog,
    AttestationRecord,
    Scroll,
    ScrollAction,
    ScrollEvidence,
    ScrollParticipants,
    blake3_hex,
    canonical_bytes,
    generate_ed25519_keypair,
    public_key_from_private_key,
    sign_ed25519,
    verify_ed25519,
)
from grid.config import MOSTAR_CLUSTER_ID


def _sealed_scroll() -> tuple[Scroll, str, str]:
    private_key, public_key = generate_ed25519_keypair()
    scroll = Scroll.create(
        cluster_pubkey=public_key,
        action=ScrollAction(
            action_type="supply_transfer",
            intent="emergency_cholera_response",
            risk_level="medium",
        ),
        participants=ScrollParticipants(
            requester_soulprint_hash=blake3_hex("requester"),
            approver_hashes=[blake3_hex("approver")],
        ),
        inputs={"clinic_id": "clinic-784", "quantity": 200},
        gate_receipts={"woo": {"status": "passed", "resonance_score": 0.91}},
        evidence=ScrollEvidence(evidence_hashes=[blake3_hex("proof-of-need")]),
        human_context={"summary": "Emergency cholera kits dispatched."},
        created_at="2026-05-27T14:32:25Z",
    ).seal_with_cluster_key(private_key)
    return scroll, private_key, public_key


def test_jcs_canonicalization_is_deterministic_for_key_order():
    first = {"b": 2, "a": 1}
    second = {"a": 1, "b": 2}

    assert canonical_bytes(first) == canonical_bytes(second)


def test_jcs_canonicalization_omits_whitespace():
    assert canonical_bytes({"a": 1, "b": [2, 3]}) == b'{"a":1,"b":[2,3]}'


def test_blake3_empty_known_vector():
    assert blake3_hex(b"") == "af1349b9f5f9a1a6a0404dea36dcc9499bcb25c9adc112b7cc9a93cae41f3262"


@pytest.mark.parametrize("payload", ["abc", b"abc", "MoStar"])
def test_blake3_hex_returns_64_char_hex(payload):
    digest = blake3_hex(payload)

    assert len(digest) == 64
    assert int(digest, 16) >= 0


def test_ed25519_generated_public_key_matches_private_key():
    private_key, public_key = generate_ed25519_keypair()

    assert public_key_from_private_key(private_key) == public_key


def test_ed25519_signature_verifies():
    private_key, public_key = generate_ed25519_keypair()
    message = b"sealed-scroll-hash"

    signature = sign_ed25519(private_key, message)

    assert verify_ed25519(public_key, signature, message)


def test_ed25519_signature_rejects_tampered_message():
    private_key, public_key = generate_ed25519_keypair()
    signature = sign_ed25519(private_key, b"sealed-scroll-hash")

    assert not verify_ed25519(public_key, signature, b"tampered")


def test_ed25519_signature_rejects_wrong_public_key():
    private_key, _ = generate_ed25519_keypair()
    _, other_public_key = generate_ed25519_keypair()
    signature = sign_ed25519(private_key, b"sealed-scroll-hash")

    assert not verify_ed25519(other_public_key, signature, b"sealed-scroll-hash")


def test_scroll_create_uses_canonical_versions_and_cluster_id():
    scroll, _, _ = _sealed_scroll()

    assert scroll.scroll_version == "1.0.0"
    assert scroll.schema_version == "4.0a"
    assert scroll.cluster.cluster_id == MOSTAR_CLUSTER_ID
    assert scroll.scroll_id.startswith(f"scr-{MOSTAR_CLUSTER_ID}-")


def test_scroll_to_dict_contains_required_top_level_fields():
    scroll, _, _ = _sealed_scroll()

    assert set(scroll.to_dict()) == {
        "scroll_version",
        "scroll_id",
        "schema_version",
        "cluster",
        "action",
        "participants",
        "inputs",
        "gate_receipts",
        "evidence",
        "human_context",
        "attestations",
        "seal",
        "lifecycle",
    }


def test_scroll_unsigned_payload_clears_seal_material():
    scroll, _, _ = _sealed_scroll()
    unsigned = scroll.unsigned_payload()

    assert unsigned["seal"]["seal_hash"] == ""
    assert unsigned["seal"]["cluster_signatures"] == []


def test_scroll_seal_hash_is_stable_without_mutation():
    scroll, _, _ = _sealed_scroll()

    assert scroll.seal_hash() == scroll.seal_hash()


def test_scroll_seal_hash_changes_when_inputs_change():
    scroll, _, _ = _sealed_scroll()
    original = scroll.seal_hash()

    scroll.inputs["quantity"] = 201

    assert scroll.seal_hash() != original


def test_scroll_seal_with_cluster_key_populates_hash_and_signature():
    scroll, _, _ = _sealed_scroll()

    assert len(scroll.seal.seal_hash) == 64
    assert len(scroll.seal.cluster_signatures) == 1
    assert scroll.seal.seal_algorithm == "blake3"
    assert scroll.seal.signature_algorithm == "ed25519"


def test_scroll_signature_verifies_after_seal():
    scroll, _, _ = _sealed_scroll()

    assert scroll.verify_cluster_signature()


def test_scroll_signature_fails_after_payload_tamper():
    scroll, _, _ = _sealed_scroll()

    scroll.human_context["summary"] = "Tampered summary"

    assert not scroll.verify_cluster_signature()


def test_scroll_signature_fails_without_signature():
    scroll, _, _ = _sealed_scroll()
    scroll.seal.cluster_signatures = []

    assert not scroll.verify_cluster_signature()


def test_scroll_from_dict_round_trips():
    scroll, _, _ = _sealed_scroll()

    round_trip = Scroll.from_dict(json.loads(json.dumps(scroll.to_dict())))

    assert round_trip.to_dict() == scroll.to_dict()
    assert round_trip.verify_cluster_signature()


def test_full_scroll_envelope_seals_and_verifies_on_fresh_instance():
    scroll, _, _ = _sealed_scroll()

    fresh = Scroll.from_dict(scroll.to_dict())

    assert fresh.scroll_version == "1.0.0"
    assert fresh.schema_version == "4.0a"
    assert fresh.seal.seal_algorithm == "blake3"
    assert fresh.seal.signature_algorithm == "ed25519"
    assert fresh.verify_cluster_signature()


def test_scroll_append_attestation_preserves_existing_seal_verification():
    scroll, _, _ = _sealed_scroll()
    scroll.append_attestation({"cluster_id": "kampala-beta", "signature": "sig"})

    assert scroll.attestations[0]["cluster_id"] == "kampala-beta"
    assert scroll.verify_cluster_signature()


def test_scroll_revocation_flag_set_correctly():
    scroll, _, _ = _sealed_scroll()

    scroll.revoke("superseded by counter-scroll")

    assert scroll.lifecycle.status == "revoked"
    assert scroll.lifecycle.revoked is True
    assert scroll.lifecycle.revocation_reason == "superseded by counter-scroll"


def test_guardian_multi_sig_requires_two_signatures():
    scroll, private_key, _ = _sealed_scroll()

    assert not scroll.verify_cluster_signatures(min_signatures=2)

    scroll.add_cluster_signature(private_key)

    assert len(scroll.seal.cluster_signatures) == 2
    assert scroll.verify_cluster_signatures(min_signatures=2)


@pytest.mark.parametrize("risk_level", ["low", "medium", "high"])
def test_scroll_supports_risk_levels(risk_level):
    private_key, public_key = generate_ed25519_keypair()
    scroll = Scroll.create(
        cluster_pubkey=public_key,
        action=ScrollAction(action_type="test", intent="test", risk_level=risk_level),
        participants=ScrollParticipants(requester_soulprint_hash=blake3_hex("r")),
        inputs={},
        gate_receipts={},
    ).seal_with_cluster_key(private_key)

    assert scroll.action.risk_level == risk_level
    assert scroll.verify_cluster_signature()


def test_attestation_log_creates_cluster_scoped_paths(tmp_path):
    log = AttestationLog(tmp_path / "clusters" / "nairobi-alpha")

    assert log.given_path.as_posix().endswith("clusters/nairobi-alpha/attestations_given.jsonl")
    assert log.received_path.as_posix().endswith("clusters/nairobi-alpha/attestations_received.jsonl")
    assert log.disputed_path.as_posix().endswith("clusters/nairobi-alpha/disputed_scrolls.jsonl")


def test_attestation_log_records_given(tmp_path):
    log = AttestationLog(tmp_path / "cluster")
    record = _attestation("given")

    log.record_given(record)

    assert log.read_given()[0]["direction"] == "given"
    assert log.read_given()[0]["cluster_id"] == MOSTAR_CLUSTER_ID
    assert log.read_given()[0]["cluster_receiving"] == "kampala-beta"


def test_attestation_log_records_received(tmp_path):
    log = AttestationLog(tmp_path / "cluster")
    record = _attestation("received")

    log.record_received(record)

    assert log.read_received()[0]["direction"] == "received"
    assert log.read_received()[0]["cluster_attesting"] == "kampala-beta"


def test_attestation_log_records_disputed(tmp_path):
    log = AttestationLog(tmp_path / "cluster")
    record = _attestation("received", status="disputed")

    log.record_dispute(record)

    assert log.read_disputed()[0]["status"] == "disputed"


def test_attestation_log_is_append_only(tmp_path):
    log = AttestationLog(tmp_path / "cluster")

    log.record_given(_attestation("given", peer_cluster_id="kampala-beta"))
    log.record_given(_attestation("given", peer_cluster_id="lagos-gamma"))

    assert [r["cluster_receiving"] for r in log.read_given()] == ["kampala-beta", "lagos-gamma"]


def test_attestation_log_rejects_wrong_given_direction(tmp_path):
    log = AttestationLog(tmp_path / "cluster")

    with pytest.raises(ValueError):
        log.record_given(_attestation("received"))


def test_attestation_log_rejects_wrong_received_direction(tmp_path):
    log = AttestationLog(tmp_path / "cluster")

    with pytest.raises(ValueError):
        log.record_received(_attestation("given"))


def test_attestation_log_rejects_non_disputed_dispute_record(tmp_path):
    log = AttestationLog(tmp_path / "cluster")

    with pytest.raises(ValueError):
        log.record_dispute(_attestation("received", status="accepted"))


def test_attestation_record_to_dict_has_required_fields():
    record = _attestation("given")

    assert set(record.to_dict()) == {
        "timestamp",
        "cluster_id",
        "scroll_id",
        "cluster_receiving",
        "signature",
        "scroll_hash",
        "status",
        "direction",
    }


def test_received_attestation_record_uses_cluster_attesting_field():
    record = _attestation("received")

    assert "cluster_attesting" in record.to_dict()
    assert "cluster_receiving" not in record.to_dict()


def test_attestation_read_empty_logs_returns_empty_lists(tmp_path):
    log = AttestationLog(tmp_path / "cluster")

    assert log.read_given() == []
    assert log.read_received() == []
    assert log.read_disputed() == []


def test_attestation_jsonl_lines_are_valid_json(tmp_path):
    log = AttestationLog(tmp_path / "cluster")
    log.record_given(_attestation("given"))

    raw = Path(log.given_path).read_text(encoding="utf-8").strip()

    assert json.loads(raw)["scroll_id"] == "scr-test"


def test_evidence_hashes_are_blake3_hex_values():
    scroll, _, _ = _sealed_scroll()

    assert all(len(h) == 64 for h in scroll.evidence.evidence_hashes)


def _attestation(
    direction: str,
    *,
    status: str = "attested",
    peer_cluster_id: str = "kampala-beta",
) -> AttestationRecord:
    return AttestationRecord.create(
        scroll_id="scr-test",
        peer_cluster_id=peer_cluster_id,
        signature="signature",
        scroll_hash=blake3_hex("scroll"),
        status=status,
        direction=direction,
    )
