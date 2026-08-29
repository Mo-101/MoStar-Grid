"""Runtime tests for `mo-mind-provenance-filter-001`."""
from __future__ import annotations


def _memory(**overrides) -> dict:
    base = {
        "license_status": "permitted",
        "consent_status": "granted",
        "withdrawn": False,
        "derivation_permitted": True,
    }
    base.update(overrides)
    return base


def test_permitted_memory_allowed(engine):
    dec = engine.evaluate(
        "mo-mind-provenance-filter-001",
        _memory(),
        principal="user-1",
    )
    assert dec.decision == "ALLOW"
    assert not dec.reason_codes


def test_unlicensed_memory_filtered(engine):
    dec = engine.evaluate(
        "mo-mind-provenance-filter-001",
        _memory(license_status="denied"),
        principal="user-1",
    )
    assert dec.decision == "FILTER"
    assert "UNLICENSED" in dec.reason_codes


def test_consent_denied_filtered(engine):
    dec = engine.evaluate(
        "mo-mind-provenance-filter-001",
        _memory(consent_status="denied"),
        principal="user-1",
    )
    assert dec.decision == "FILTER"
    assert "CONSENT_DENIED" in dec.reason_codes


def test_withdrawn_memory_filtered(engine):
    dec = engine.evaluate(
        "mo-mind-provenance-filter-001",
        _memory(withdrawn=True),
        principal="user-1",
    )
    assert dec.decision == "FILTER"
    assert "WITHDRAWN" in dec.reason_codes


def test_derivation_limited_filtered(engine):
    dec = engine.evaluate(
        "mo-mind-provenance-filter-001",
        _memory(
            derivation_permitted=False,
            inference_purpose="marketing",
            allowed_purposes=["research"],
        ),
        principal="user-1",
    )
    assert dec.decision == "FILTER"
    assert "DERIVATION_LIMITED" in dec.reason_codes
