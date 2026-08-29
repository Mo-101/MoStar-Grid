"""Runtime tests for `mo-mind-conduit-001`."""
from __future__ import annotations


def test_unbound_invocation_denied(engine):
    dec = engine.evaluate(
        "mo-mind-conduit-001",
        {
            "caller": "user-1",
            "model_runtime": "phi-4",
        },
        principal="user-1",
    )
    assert dec.decision == "DENY"
    assert "UNBOUND_INVOCATION" in dec.reason_codes


def test_unauthorized_invocation_denied(engine):
    dec = engine.evaluate(
        "mo-mind-conduit-001",
        {
            "caller": "user-1",
            "model_runtime": "phi-4",
            "binding": {"id": "b1", "sealed": True},
            "authority": {"approved": False},
        },
        principal="user-1",
    )
    assert dec.decision == "DENY"
    assert "UNAUTHORIZED_INVOCATION" in dec.reason_codes


def test_approved_invocation_allowed(engine):
    dec = engine.evaluate(
        "mo-mind-conduit-001",
        {
            "caller": "user-1",
            "model_runtime": "phi-4",
            "binding": {"id": "b1", "sealed": True},
            "authority": {"approved": True},
        },
        principal="user-1",
    )
    assert dec.decision == "ALLOW"
    assert not dec.reason_codes


def test_application_cannot_bypass_wrapper(engine):
    dec = engine.evaluate(
        "mo-mind-conduit-001",
        {
            "caller": "user-1",
            "model_runtime": "phi-4",
            "binding": "direct",
            "authority": {"approved": True},
        },
        principal="user-1",
    )
    assert dec.decision == "DENY"
    assert "UNBOUND_INVOCATION" in dec.reason_codes
