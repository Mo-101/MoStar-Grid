"""Bridge Woo judgment into the MoScript RuntimeManager execution path."""
from __future__ import annotations

import pathlib
import uuid

import pytest

from core.protocols.moscript.runtime import RuntimeManager, RuntimeState


PROJECT_ROOT = pathlib.Path(__file__).parent.parent.parent.parent.resolve()
CONTRACTS_DIR = PROJECT_ROOT / "core" / "protocols" / "moscript" / "contracts"
BINARY = PROJECT_ROOT / "core" / "protocols" / "moscript" / "moscript-v0.1.1-linux-amd64"
ARITHMETIC_MS = pathlib.Path(__file__).parent / "fixtures" / "arithmetic.ms"


def _conduit_allow_event(principal: str) -> dict:
    return {
        "binding": {"sealed": True},
        "authority": {"approved": True},
        "caller": principal,
        "model_runtime": "local",
    }


def _approved_woo() -> dict:
    return {
        "approved": True,
        "confidence": 0.985,
        "threshold": 0.97,
        "scores": {
            "ikang": 0.95,
            "mmong": 0.95,
            "afim": 0.95,
            "isong": 0.95,
        },
        "afim_floor": 0.0,
        "afim_floor_passed": True,
        "reasoning": "Woo approved; compound confidence above threshold.",
        "judged_at": "2026-09-02T19:24:49.113729+00:00",
    }


def _denied_woo() -> dict:
    return {
        "approved": False,
        "confidence": 0.745,
        "threshold": 0.97,
        "scores": {
            "ikang": 0.85,
            "mmong": 0.85,
            "afim": 0.85,
            "isong": 0.55,
        },
        "afim_floor": 0.0,
        "afim_floor_passed": True,
        "reasoning": "Compound confidence below Woo seal threshold.",
        "judged_at": "2026-09-02T19:24:49.113729+00:00",
    }


def _manager(tmp_path: pathlib.Path) -> RuntimeManager:
    return RuntimeManager(
        contracts_dir=CONTRACTS_DIR,
        moscript_bin=BINARY,
        workspace=tmp_path / "workspace",
    )


@pytest.fixture
def manager(tmp_path: pathlib.Path) -> RuntimeManager:
    return _manager(tmp_path)


def test_woo_approved_allows_execution(manager: RuntimeManager):
    result = manager.execute(
        artifact_path=ARITHMETIC_MS,
        principal="tester",
        governing_contracts=["mo-mind-conduit-001"],
        governing_events={"mo-mind-conduit-001": _conduit_allow_event("tester")},
        woo_judgment=_approved_woo(),
    )

    assert result.state is RuntimeState.COMPLETED
    assert result.exit_code == 0
    assert "14" in result.stdout
    assert result.attestation is not None
    assert RuntimeState.DENIED not in [t["state"] for t in result.transitions]


def test_woo_denied_blocks_before_supervisor(
    manager: RuntimeManager, monkeypatch: pytest.MonkeyPatch
):
    run_calls: list[tuple] = []

    def fake_run(*args, **kwargs):
        run_calls.append((args, kwargs))
        return (0, "", "", {}, {})

    monkeypatch.setattr(manager, "_run", fake_run)

    result = manager.execute(
        artifact_path=ARITHMETIC_MS,
        principal="tester",
        governing_contracts=["mo-mind-conduit-001"],
        governing_events={"mo-mind-conduit-001": _conduit_allow_event("tester")},
        woo_judgment=_denied_woo(),
    )

    assert result.state is RuntimeState.DENIED
    assert not run_calls, "_run must not be invoked after a Woo denial"
    assert RuntimeState.RUNNING not in [t["state"] for t in result.transitions]
    assert RuntimeState.COMPLETED not in [t["state"] for t in result.transitions]


def test_woo_denied_persists_trace(manager: RuntimeManager):
    woo = _denied_woo()
    result = manager.execute(
        artifact_path=ARITHMETIC_MS,
        principal="tester",
        governing_contracts=["mo-mind-conduit-001"],
        governing_events={"mo-mind-conduit-001": _conduit_allow_event("tester")},
        woo_judgment=woo,
    )

    assert result.state is RuntimeState.DENIED
    assert result.provenance is not None
    assert result.provenance.stored
    assert result.attestation is not None
    assert result.attestation.decision == "DENY"
    assert result.attestation_id == result.attestation.attestation_id
    assert result.evidence["audit"]["woo_judgment"] == woo
    assert result.evidence["audit"]["woo_judgment"]["confidence"] == 0.745
    assert result.evidence["audit"]["woo_judgment"]["afim_floor_passed"] is True
    assert result.evidence["audit"]["woo_judgment"]["reasoning"]


def test_woo_missing_is_explicit(manager: RuntimeManager):
    result = manager.execute(
        artifact_path=ARITHMETIC_MS,
        principal="tester",
        governing_contracts=["mo-mind-conduit-001"],
        governing_events={"mo-mind-conduit-001": _conduit_allow_event("tester")},
    )

    assert result.state is RuntimeState.COMPLETED
    assert "woo_judgment" not in result.evidence["audit"]
    assert result.attestation is not None
    assert result.attestation.decision == "ALLOW"


def test_replay_still_applies_to_woo_denied_execution(manager: RuntimeManager):
    execution_id = str(uuid.uuid4())
    woo = _denied_woo()

    first = manager.execute(
        artifact_path=ARITHMETIC_MS,
        principal="tester",
        governing_contracts=["mo-mind-conduit-001"],
        governing_events={"mo-mind-conduit-001": _conduit_allow_event("tester")},
        execution_id=execution_id,
        woo_judgment=woo,
    )
    assert first.state is RuntimeState.DENIED
    assert first.attestation is not None
    first_attestation_id = first.attestation.attestation_id

    second = manager.execute(
        artifact_path=ARITHMETIC_MS,
        principal="tester",
        governing_contracts=["mo-mind-conduit-001"],
        governing_events={"mo-mind-conduit-001": _conduit_allow_event("tester")},
        execution_id=execution_id,
        woo_judgment=woo,
    )
    assert second.state is RuntimeState.FAILED
    assert second.failure is not None
    assert second.failure["reason"] == "REPLAY_DETECTED"
    assert second.attestation is not None
    assert second.attestation.attestation_id == first_attestation_id
