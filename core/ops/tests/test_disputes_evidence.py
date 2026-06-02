from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
import pytest

from federation import (
    ClusterKeyRegistry,
    DisputeError,
    DisputeLog,
    EvidenceForbidden,
    EvidenceGateway,
    EvidenceNotFound,
    EvidenceRateLimited,
    EvidenceRateLimiter,
    EvidenceStore,
    EvidenceUnauthorized,
    InvalidDisputeReason,
    InvalidDisputeSignature,
    InvalidDisputeStatus,
    blake3_hex,
    dispute_signing_bytes,
    generate_ed25519_keypair,
    sign_ed25519,
)
from grid.api import app
from grid.config import MOSTAR_CLUSTER_ID


SCROLL_ID = "scr-kampala-beta-20260527T143225Z-demo"
REMOTE_CLUSTER = "kampala-beta"


def _time(offset_days: int = 0) -> str:
    return (
        (datetime.now(timezone.utc) + timedelta(days=offset_days))
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _signed_dispute(private_key: str, **overrides) -> dict:
    payload = {
        "dispute_id": f"dsp-{MOSTAR_CLUSTER_ID}-20260527-001",
        "scroll_id": SCROLL_ID,
        "disputing_cluster_id": MOSTAR_CLUSTER_ID,
        "reason": "anomaly_detected",
        "details": "Quantity unusually high for cholera response.",
        "severity": "medium",
        "status": "active",
        "registered_at": _time(0),
        "expires_at": _time(30),
    }
    payload.update(overrides)
    payload["signature"] = sign_ed25519(private_key, dispute_signing_bytes(payload))
    return payload


def _log(tmp_path, public_key: str) -> DisputeLog:
    registry = ClusterKeyRegistry(keys={MOSTAR_CLUSTER_ID: public_key})
    return DisputeLog(tmp_path / "clusters" / REMOTE_CLUSTER, registry)


def test_register_dispute_verifies_signature_before_store(tmp_path):
    private_key, public_key = generate_ed25519_keypair()
    dispute = _signed_dispute(private_key)
    log = _log(tmp_path, public_key)

    result = log.register_dispute(dispute)

    assert result["created"] is True
    assert log.read_disputes_received()[0]["signature"] == dispute["signature"]


def test_register_dispute_rejects_invalid_signature_and_does_not_store(tmp_path):
    private_key, public_key = generate_ed25519_keypair()
    dispute = _signed_dispute(private_key)
    dispute["details"] = "tampered after signing"
    log = _log(tmp_path, public_key)

    with pytest.raises(InvalidDisputeSignature):
        log.register_dispute(dispute)

    assert log.read_disputes_received() == []
    assert not log.path.exists()


def test_register_dispute_rejects_unknown_disputing_cluster_key(tmp_path):
    private_key, _ = generate_ed25519_keypair()
    dispute = _signed_dispute(private_key)
    log = DisputeLog(tmp_path / "clusters" / REMOTE_CLUSTER, ClusterKeyRegistry(keys={}))

    with pytest.raises(InvalidDisputeSignature, match="unknown_disputing_cluster_key"):
        log.register_dispute(dispute)


def test_register_dispute_is_idempotent_for_active_pair(tmp_path):
    private_key, public_key = generate_ed25519_keypair()
    log = _log(tmp_path, public_key)
    first = _signed_dispute(private_key, dispute_id="dsp-first")
    second = _signed_dispute(private_key, dispute_id="dsp-second")

    first_result = log.register_dispute(first)
    second_result = log.register_dispute(second)

    assert first_result["created"] is True
    assert second_result["created"] is False
    assert second_result["dispute_id"] == "dsp-first"
    assert len(log.read_disputes_received()) == 1


def test_register_dispute_allows_new_after_expiration(tmp_path):
    private_key, public_key = generate_ed25519_keypair()
    log = _log(tmp_path, public_key)
    expired = _signed_dispute(
        private_key,
        dispute_id="dsp-expired",
        registered_at=_time(-40),
        expires_at=_time(-10),
    )
    fresh = _signed_dispute(private_key, dispute_id="dsp-fresh")

    log.register_dispute(expired)
    result = log.register_dispute(fresh)

    assert result["created"] is True
    assert result["dispute_id"] == "dsp-fresh"
    assert len(log.read_disputes_received()) == 2


@pytest.mark.parametrize(
    "reason",
    [
        "anomaly_detected",
        "insufficient_evidence",
        "governance_violation",
        "quality_concern",
        "timeline_mismatch",
        "other",
    ],
)
def test_register_dispute_accepts_valid_reasons(tmp_path, reason):
    private_key, public_key = generate_ed25519_keypair()
    dispute = _signed_dispute(private_key, reason=reason)
    result = _log(tmp_path, public_key).register_dispute(dispute)

    assert result["created"] is True


def test_register_dispute_rejects_invalid_reason(tmp_path):
    private_key, public_key = generate_ed25519_keypair()
    dispute = _signed_dispute(private_key, reason="bad_reason")

    with pytest.raises(InvalidDisputeReason):
        _log(tmp_path, public_key).register_dispute(dispute)


def test_register_dispute_rejects_non_active_status(tmp_path):
    private_key, public_key = generate_ed25519_keypair()
    dispute = _signed_dispute(private_key, status="resolved")

    with pytest.raises(InvalidDisputeStatus):
        _log(tmp_path, public_key).register_dispute(dispute)


def test_can_access_evidence_requires_active_unexpired_dispute(tmp_path):
    private_key, public_key = generate_ed25519_keypair()
    log = _log(tmp_path, public_key)
    log.register_dispute(_signed_dispute(private_key))

    assert log.can_access_evidence(cluster_id=MOSTAR_CLUSTER_ID, scroll_id=SCROLL_ID)


def test_can_access_evidence_rejects_expired_dispute(tmp_path):
    private_key, public_key = generate_ed25519_keypair()
    log = _log(tmp_path, public_key)
    log.register_dispute(
        _signed_dispute(private_key, registered_at=_time(-40), expires_at=_time(-10))
    )

    assert not log.can_access_evidence(cluster_id=MOSTAR_CLUSTER_ID, scroll_id=SCROLL_ID)


def test_high_severity_active_dispute_freezes_finalization(tmp_path):
    private_key, public_key = generate_ed25519_keypair()
    log = _log(tmp_path, public_key)
    log.register_dispute(_signed_dispute(private_key, severity="high"))

    assert not log.can_finalize_scroll(SCROLL_ID)


def test_low_severity_active_dispute_does_not_freeze_finalization(tmp_path):
    private_key, public_key = generate_ed25519_keypair()
    log = _log(tmp_path, public_key)
    log.register_dispute(_signed_dispute(private_key, severity="low"))

    assert log.can_finalize_scroll(SCROLL_ID)


def test_evidence_gateway_requires_requester_signature(tmp_path):
    private_key, public_key = generate_ed25519_keypair()
    log = _log(tmp_path, public_key)
    log.register_dispute(_signed_dispute(private_key))
    store = EvidenceStore(tmp_path / "evidence")
    store.write_manifest(SCROLL_ID, [_evidence_ref()])
    gateway = EvidenceGateway(
        dispute_log=log,
        evidence_store=store,
        key_registry=ClusterKeyRegistry(keys={MOSTAR_CLUSTER_ID: public_key}),
    )

    with pytest.raises(EvidenceUnauthorized):
        gateway.get_evidence(
            scroll_id=SCROLL_ID,
            requester_cluster_id=MOSTAR_CLUSTER_ID,
            signature="bad-signature",
        )


def test_evidence_gateway_requires_active_dispute(tmp_path):
    private_key, public_key = generate_ed25519_keypair()
    store = EvidenceStore(tmp_path / "evidence")
    store.write_manifest(SCROLL_ID, [_evidence_ref()])
    gateway = EvidenceGateway(
        dispute_log=_log(tmp_path, public_key),
        evidence_store=store,
        key_registry=ClusterKeyRegistry(keys={MOSTAR_CLUSTER_ID: public_key}),
    )

    with pytest.raises(EvidenceForbidden):
        gateway.get_evidence(
            scroll_id=SCROLL_ID,
            requester_cluster_id=MOSTAR_CLUSTER_ID,
            signature=sign_ed25519(private_key, SCROLL_ID.encode("utf-8")),
        )


def test_evidence_gateway_returns_references_only(tmp_path):
    private_key, public_key = generate_ed25519_keypair()
    log = _log(tmp_path, public_key)
    dispute = _signed_dispute(private_key)
    log.register_dispute(dispute)
    store = EvidenceStore(tmp_path / "evidence")
    store.write_manifest(SCROLL_ID, [_evidence_ref()])
    gateway = EvidenceGateway(
        dispute_log=log,
        evidence_store=store,
        key_registry=ClusterKeyRegistry(keys={MOSTAR_CLUSTER_ID: public_key}),
    )

    result = gateway.get_evidence(
        scroll_id=SCROLL_ID,
        requester_cluster_id=MOSTAR_CLUSTER_ID,
        signature=sign_ed25519(private_key, SCROLL_ID.encode("utf-8")),
    )

    assert result["dispute_id"] == dispute["dispute_id"]
    assert result["evidence"][0]["evidence_hash"] == blake3_hex("proof")
    assert "blob" not in result["evidence"][0]


def test_evidence_gateway_404_when_manifest_missing_after_active_dispute(tmp_path):
    private_key, public_key = generate_ed25519_keypair()
    log = _log(tmp_path, public_key)
    log.register_dispute(_signed_dispute(private_key))
    gateway = EvidenceGateway(
        dispute_log=log,
        evidence_store=EvidenceStore(tmp_path / "evidence"),
        key_registry=ClusterKeyRegistry(keys={MOSTAR_CLUSTER_ID: public_key}),
    )

    with pytest.raises(EvidenceNotFound):
        gateway.get_evidence(
            scroll_id=SCROLL_ID,
            requester_cluster_id=MOSTAR_CLUSTER_ID,
            signature=sign_ed25519(private_key, SCROLL_ID.encode("utf-8")),
        )


def test_evidence_gateway_rate_limits_per_cluster(tmp_path):
    private_key, public_key = generate_ed25519_keypair()
    log = _log(tmp_path, public_key)
    log.register_dispute(_signed_dispute(private_key))
    store = EvidenceStore(tmp_path / "evidence")
    store.write_manifest(SCROLL_ID, [_evidence_ref()])
    gateway = EvidenceGateway(
        dispute_log=log,
        evidence_store=store,
        key_registry=ClusterKeyRegistry(keys={MOSTAR_CLUSTER_ID: public_key}),
        rate_limiter=EvidenceRateLimiter(max_requests=1),
    )
    signature = sign_ed25519(private_key, SCROLL_ID.encode("utf-8"))

    gateway.get_evidence(scroll_id=SCROLL_ID, requester_cluster_id=MOSTAR_CLUSTER_ID, signature=signature)
    with pytest.raises(EvidenceRateLimited):
        gateway.get_evidence(scroll_id=SCROLL_ID, requester_cluster_id=MOSTAR_CLUSTER_ID, signature=signature)


def test_api_register_dispute_and_evidence_flow(tmp_path, monkeypatch):
    private_key, public_key = generate_ed25519_keypair()
    dispute_log = _log(tmp_path, public_key)
    store = EvidenceStore(tmp_path / "evidence")
    store.write_manifest(SCROLL_ID, [_evidence_ref()])
    monkeypatch.setattr("grid.api.DisputeLog", lambda: dispute_log)
    monkeypatch.setattr(
        "grid.api.EvidenceGateway",
        lambda: EvidenceGateway(
            dispute_log=dispute_log,
            evidence_store=store,
            key_registry=ClusterKeyRegistry(keys={MOSTAR_CLUSTER_ID: public_key}),
        ),
    )
    client = TestClient(app)
    dispute = _signed_dispute(private_key)

    register_response = client.post("/api/disputes/register", json={"dispute": dispute})
    evidence_response = client.get(
        f"/api/evidence/{SCROLL_ID}",
        params={
            "requester_cluster_id": MOSTAR_CLUSTER_ID,
            "signature": sign_ed25519(private_key, SCROLL_ID.encode("utf-8")),
        },
    )

    assert register_response.status_code == 200
    assert register_response.json()["created"] is True
    assert evidence_response.status_code == 200
    assert evidence_response.json()["evidence"][0]["retrieval_url"].endswith("/blob/0")


def test_api_evidence_returns_403_without_dispute(tmp_path, monkeypatch):
    private_key, public_key = generate_ed25519_keypair()
    monkeypatch.setattr(
        "grid.api.EvidenceGateway",
        lambda: EvidenceGateway(
            dispute_log=_log(tmp_path, public_key),
            evidence_store=EvidenceStore(tmp_path / "evidence"),
            key_registry=ClusterKeyRegistry(keys={MOSTAR_CLUSTER_ID: public_key}),
        ),
    )
    response = TestClient(app).get(
        f"/api/evidence/{SCROLL_ID}",
        params={
            "requester_cluster_id": MOSTAR_CLUSTER_ID,
            "signature": sign_ed25519(private_key, SCROLL_ID.encode("utf-8")),
        },
    )

    assert response.status_code == 403


@pytest.mark.parametrize(
    "field",
    [
        "dispute_id",
        "scroll_id",
        "disputing_cluster_id",
        "reason",
        "details",
        "severity",
        "signature",
    ],
)
def test_register_dispute_rejects_missing_required_fields(tmp_path, field):
    private_key, public_key = generate_ed25519_keypair()
    dispute = _signed_dispute(private_key)
    dispute.pop(field)

    with pytest.raises(DisputeError):
        _log(tmp_path, public_key).register_dispute(dispute)


@pytest.mark.parametrize("severity", ["critical", "", "MEDIUM"])
def test_register_dispute_rejects_invalid_severity(tmp_path, severity):
    private_key, public_key = generate_ed25519_keypair()
    dispute = _signed_dispute(private_key, severity=severity)

    with pytest.raises(DisputeError, match="invalid_dispute_severity"):
        _log(tmp_path, public_key).register_dispute(dispute)


def test_register_dispute_rejects_expiration_equal_to_registration(tmp_path):
    private_key, public_key = generate_ed25519_keypair()
    timestamp = _time(0)
    dispute = _signed_dispute(private_key, registered_at=timestamp, expires_at=timestamp)

    with pytest.raises(DisputeError, match="dispute_expiration_must_be_after_registration"):
        _log(tmp_path, public_key).register_dispute(dispute)


def test_register_dispute_rejects_expiration_before_registration(tmp_path):
    private_key, public_key = generate_ed25519_keypair()
    dispute = _signed_dispute(private_key, registered_at=_time(1), expires_at=_time(0))

    with pytest.raises(DisputeError, match="dispute_expiration_must_be_after_registration"):
        _log(tmp_path, public_key).register_dispute(dispute)


def test_idempotency_is_scoped_to_scroll_id(tmp_path):
    private_key, public_key = generate_ed25519_keypair()
    log = _log(tmp_path, public_key)
    first = _signed_dispute(private_key, dispute_id="dsp-one")
    second = _signed_dispute(
        private_key,
        dispute_id="dsp-two",
        scroll_id="scr-kampala-beta-20260527T143225Z-other",
    )

    log.register_dispute(first)
    result = log.register_dispute(second)

    assert result["created"] is True
    assert len(log.read_disputes_received()) == 2


def test_idempotency_is_scoped_to_disputing_cluster(tmp_path):
    first_private, first_public = generate_ed25519_keypair()
    second_private, second_public = generate_ed25519_keypair()
    log = DisputeLog(
        tmp_path / "clusters" / REMOTE_CLUSTER,
        ClusterKeyRegistry(keys={MOSTAR_CLUSTER_ID: first_public, "lagos-beta": second_public}),
    )

    log.register_dispute(_signed_dispute(first_private, dispute_id="dsp-nairobi"))
    result = log.register_dispute(
        _signed_dispute(
            second_private,
            dispute_id="dsp-lagos",
            disputing_cluster_id="lagos-beta",
        )
    )

    assert result["created"] is True
    assert len(log.read_disputes_received()) == 2


def test_can_access_evidence_rejects_wrong_cluster(tmp_path):
    private_key, public_key = generate_ed25519_keypair()
    log = _log(tmp_path, public_key)
    log.register_dispute(_signed_dispute(private_key))

    assert not log.can_access_evidence(cluster_id="lagos-beta", scroll_id=SCROLL_ID)


def test_can_access_evidence_rejects_wrong_scroll(tmp_path):
    private_key, public_key = generate_ed25519_keypair()
    log = _log(tmp_path, public_key)
    log.register_dispute(_signed_dispute(private_key))

    assert not log.can_access_evidence(cluster_id=MOSTAR_CLUSTER_ID, scroll_id="scr-other")


def test_active_dispute_returns_stored_notice(tmp_path):
    private_key, public_key = generate_ed25519_keypair()
    log = _log(tmp_path, public_key)
    dispute = _signed_dispute(private_key, dispute_id="dsp-active")
    log.register_dispute(dispute)

    active = log.active_dispute(cluster_id=MOSTAR_CLUSTER_ID, scroll_id=SCROLL_ID)

    assert active["dispute_id"] == "dsp-active"
    assert active["reason"] == "anomaly_detected"


def test_can_finalize_ignores_expired_high_severity_dispute(tmp_path):
    private_key, public_key = generate_ed25519_keypair()
    log = _log(tmp_path, public_key)
    log.register_dispute(
        _signed_dispute(
            private_key,
            severity="high",
            registered_at=_time(-40),
            expires_at=_time(-10),
        )
    )

    assert log.can_finalize_scroll(SCROLL_ID)


def test_evidence_gateway_rejects_unknown_requester_key(tmp_path):
    private_key, public_key = generate_ed25519_keypair()
    log = _log(tmp_path, public_key)
    log.register_dispute(_signed_dispute(private_key))
    gateway = EvidenceGateway(
        dispute_log=log,
        evidence_store=EvidenceStore(tmp_path / "evidence"),
        key_registry=ClusterKeyRegistry(keys={}),
    )

    with pytest.raises(EvidenceUnauthorized, match="unknown_requester_cluster_key"):
        gateway.get_evidence(
            scroll_id=SCROLL_ID,
            requester_cluster_id=MOSTAR_CLUSTER_ID,
            signature=sign_ed25519(private_key, SCROLL_ID.encode("utf-8")),
        )


def test_evidence_gateway_rejects_signature_from_different_cluster(tmp_path):
    private_key, public_key = generate_ed25519_keypair()
    other_private, other_public = generate_ed25519_keypair()
    log = _log(tmp_path, public_key)
    log.register_dispute(_signed_dispute(private_key))
    gateway = EvidenceGateway(
        dispute_log=log,
        evidence_store=EvidenceStore(tmp_path / "evidence"),
        key_registry=ClusterKeyRegistry(keys={MOSTAR_CLUSTER_ID: public_key, "lagos-beta": other_public}),
    )

    with pytest.raises(EvidenceUnauthorized, match="invalid_requester_signature"):
        gateway.get_evidence(
            scroll_id=SCROLL_ID,
            requester_cluster_id=MOSTAR_CLUSTER_ID,
            signature=sign_ed25519(other_private, SCROLL_ID.encode("utf-8")),
        )


def test_evidence_gateway_rejects_expired_dispute(tmp_path):
    private_key, public_key = generate_ed25519_keypair()
    log = _log(tmp_path, public_key)
    log.register_dispute(
        _signed_dispute(private_key, registered_at=_time(-40), expires_at=_time(-10))
    )
    store = EvidenceStore(tmp_path / "evidence")
    store.write_manifest(SCROLL_ID, [_evidence_ref()])
    gateway = EvidenceGateway(
        dispute_log=log,
        evidence_store=store,
        key_registry=ClusterKeyRegistry(keys={MOSTAR_CLUSTER_ID: public_key}),
    )

    with pytest.raises(EvidenceForbidden):
        gateway.get_evidence(
            scroll_id=SCROLL_ID,
            requester_cluster_id=MOSTAR_CLUSTER_ID,
            signature=sign_ed25519(private_key, SCROLL_ID.encode("utf-8")),
        )


def test_evidence_rate_limiter_resets_after_window():
    limiter = EvidenceRateLimiter(max_requests=1, window_seconds=10)
    now = datetime(2026, 5, 27, tzinfo=timezone.utc)

    assert limiter.allow(MOSTAR_CLUSTER_ID, now=now)
    assert not limiter.allow(MOSTAR_CLUSTER_ID, now=now + timedelta(seconds=5))
    assert limiter.allow(MOSTAR_CLUSTER_ID, now=now + timedelta(seconds=11))


def test_evidence_rate_limiter_is_per_cluster():
    limiter = EvidenceRateLimiter(max_requests=1, window_seconds=60)
    now = datetime(2026, 5, 27, tzinfo=timezone.utc)

    assert limiter.allow(MOSTAR_CLUSTER_ID, now=now)
    assert limiter.allow("lagos-beta", now=now)


def test_evidence_store_round_trips_multiple_references(tmp_path):
    store = EvidenceStore(tmp_path / "evidence")
    refs = [
        _evidence_ref(),
        {
            "evidence_hash": blake3_hex("arrival"),
            "content_type": "proof_of_arrival",
            "size_bytes": 10,
            "timestamp": _time(0),
            "retrieval_url": f"/api/evidence/{SCROLL_ID}/blob/1",
        },
    ]

    store.write_manifest(SCROLL_ID, refs)

    assert store.read_manifest(SCROLL_ID) == refs


def test_evidence_store_returns_empty_manifest(tmp_path):
    store = EvidenceStore(tmp_path / "evidence")
    store.write_manifest(SCROLL_ID, [])

    assert store.read_manifest(SCROLL_ID) == []


def test_api_register_dispute_invalid_signature_returns_401(tmp_path, monkeypatch):
    private_key, public_key = generate_ed25519_keypair()
    dispute = _signed_dispute(private_key)
    dispute["details"] = "tampered"
    monkeypatch.setattr("grid.api.DisputeLog", lambda: _log(tmp_path, public_key))

    response = TestClient(app).post("/api/disputes/register", json={"dispute": dispute})

    assert response.status_code == 401


def test_api_register_dispute_invalid_reason_returns_422(tmp_path, monkeypatch):
    private_key, public_key = generate_ed25519_keypair()
    dispute = _signed_dispute(private_key, reason="not_canonical")
    monkeypatch.setattr("grid.api.DisputeLog", lambda: _log(tmp_path, public_key))

    response = TestClient(app).post("/api/disputes/register", json={"dispute": dispute})

    assert response.status_code == 422


def test_api_register_dispute_idempotent_response_returns_existing_id(tmp_path, monkeypatch):
    private_key, public_key = generate_ed25519_keypair()
    dispute_log = _log(tmp_path, public_key)
    monkeypatch.setattr("grid.api.DisputeLog", lambda: dispute_log)
    client = TestClient(app)
    first = _signed_dispute(private_key, dispute_id="dsp-existing")
    second = _signed_dispute(private_key, dispute_id="dsp-duplicate")

    first_response = client.post("/api/disputes/register", json={"dispute": first})
    second_response = client.post("/api/disputes/register", json={"dispute": second})

    assert first_response.json()["created"] is True
    assert second_response.json()["created"] is False
    assert second_response.json()["dispute_id"] == "dsp-existing"


def test_api_evidence_invalid_signature_returns_401(tmp_path, monkeypatch):
    private_key, public_key = generate_ed25519_keypair()
    log = _log(tmp_path, public_key)
    log.register_dispute(_signed_dispute(private_key))
    monkeypatch.setattr(
        "grid.api.EvidenceGateway",
        lambda: EvidenceGateway(
            dispute_log=log,
            evidence_store=EvidenceStore(tmp_path / "evidence"),
            key_registry=ClusterKeyRegistry(keys={MOSTAR_CLUSTER_ID: public_key}),
        ),
    )

    response = TestClient(app).get(
        f"/api/evidence/{SCROLL_ID}",
        params={"requester_cluster_id": MOSTAR_CLUSTER_ID, "signature": "bad-signature"},
    )

    assert response.status_code == 401


def test_api_evidence_missing_manifest_returns_404_after_active_dispute(tmp_path, monkeypatch):
    private_key, public_key = generate_ed25519_keypair()
    log = _log(tmp_path, public_key)
    log.register_dispute(_signed_dispute(private_key))
    monkeypatch.setattr(
        "grid.api.EvidenceGateway",
        lambda: EvidenceGateway(
            dispute_log=log,
            evidence_store=EvidenceStore(tmp_path / "evidence"),
            key_registry=ClusterKeyRegistry(keys={MOSTAR_CLUSTER_ID: public_key}),
        ),
    )

    response = TestClient(app).get(
        f"/api/evidence/{SCROLL_ID}",
        params={
            "requester_cluster_id": MOSTAR_CLUSTER_ID,
            "signature": sign_ed25519(private_key, SCROLL_ID.encode("utf-8")),
        },
    )

    assert response.status_code == 404


def test_api_evidence_rate_limit_returns_429(tmp_path, monkeypatch):
    private_key, public_key = generate_ed25519_keypair()
    log = _log(tmp_path, public_key)
    log.register_dispute(_signed_dispute(private_key))
    store = EvidenceStore(tmp_path / "evidence")
    store.write_manifest(SCROLL_ID, [_evidence_ref()])
    monkeypatch.setattr(
        "grid.api.EvidenceGateway",
        lambda: EvidenceGateway(
            dispute_log=log,
            evidence_store=store,
            key_registry=ClusterKeyRegistry(keys={MOSTAR_CLUSTER_ID: public_key}),
            rate_limiter=EvidenceRateLimiter(max_requests=0),
        ),
    )

    response = TestClient(app).get(
        f"/api/evidence/{SCROLL_ID}",
        params={
            "requester_cluster_id": MOSTAR_CLUSTER_ID,
            "signature": sign_ed25519(private_key, SCROLL_ID.encode("utf-8")),
        },
    )

    assert response.status_code == 429


def _evidence_ref() -> dict:
    return {
        "evidence_hash": blake3_hex("proof"),
        "content_type": "proof_of_need",
        "size_bytes": 5,
        "timestamp": _time(0),
        "retrieval_url": f"/api/evidence/{SCROLL_ID}/blob/0",
    }
