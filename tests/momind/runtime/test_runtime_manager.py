"""Hermetic end-to-end acceptance tests for the MoScript RuntimeManager."""
from __future__ import annotations

import base64
import hashlib
import json
import os
import pathlib
import signal
import subprocess
import tempfile
import time
import uuid

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption

from core.protocols.moscript.runtime import RuntimeManager, RuntimeState, verify_receipt


PROJECT_ROOT = pathlib.Path(__file__).parent.parent.parent.parent.resolve()
CONTRACTS_DIR = PROJECT_ROOT / "core" / "protocols" / "moscript" / "contracts"
BINARY = PROJECT_ROOT / "core" / "protocols" / "moscript" / "moscript-v0.1.1-linux-amd64"
FIXTURES = pathlib.Path(__file__).parent / "fixtures"
ARITHMETIC_MS = FIXTURES / "arithmetic.ms"


def _conduit_allow_event(principal: str) -> dict:
    return {
        "binding": {"sealed": True},
        "authority": {"approved": True},
        "caller": principal,
        "model_runtime": "local",
    }


def _manager(tmp_path: pathlib.Path) -> RuntimeManager:
    return RuntimeManager(
        contracts_dir=CONTRACTS_DIR,
        moscript_bin=BINARY,
        max_steps=100000,
        max_depth=64,
        workspace=tmp_path / "workspace",
    )


@pytest.fixture
def manager(tmp_path: pathlib.Path) -> RuntimeManager:
    return _manager(tmp_path)


def test_ms_allow_end_to_end(manager: RuntimeManager, tmp_path: pathlib.Path):
    result = manager.execute(
        artifact_path=ARITHMETIC_MS,
        principal="tester",
        governing_contracts=["mo-mind-conduit-001"],
        governing_events={"mo-mind-conduit-001": _conduit_allow_event("tester")},
    )

    assert result.state is RuntimeState.COMPLETED
    assert result.exit_code == 0
    assert "14" in result.stdout
    assert result.decision is not None
    assert result.decision.decision == "ALLOW"
    assert result.artifact_hash
    assert result.attestation is not None
    assert result.audit_evidence is not None

    states = [t["state"] for t in result.transitions]
    assert states == [
        "discovered",
        "staged",
        "verified",
        "governed",
        "running",
        "completed",
    ]

    # Evidence envelope sanity.
    assert result.evidence["execution_id"]
    assert result.evidence["artifact"]["program_hash"] == result.artifact_hash
    assert result.evidence["governance"]["decision"] == "ALLOW"
    assert result.evidence["state"] == "completed"
    assert result.audit_evidence["program_hash"] == result.artifact_hash
    assert result.audit_evidence["execution"]["exit_code"] == 0
    assert result.attestation is not None
    assert result.attestation.receipt_hash


def test_deny_never_invokes_go_runtime(manager: RuntimeManager, monkeypatch: pytest.MonkeyPatch):
    calls: list[tuple] = []

    def fake_run(*args, **kwargs):
        calls.append((args, kwargs))
        return (1, "", "", {})

    monkeypatch.setattr(manager, "_run", fake_run)

    result = manager.execute(
        artifact_path=ARITHMETIC_MS,
        principal="tester",
        governing_contracts=["mo-mind-conduit-001"],
        governing_events={
            # Missing binding/authority/caller/model_runtime → DENY.
            "mo-mind-conduit-001": {},
        },
    )

    assert result.state is RuntimeState.DENIED
    assert not calls, "Go runtime must not be invoked after a DENY decision"
    assert result.stdout == ""
    assert result.attestation is None


def test_sealed_scroll_end_to_end(manager: RuntimeManager, tmp_path: pathlib.Path):
    priv = tmp_path / "private.key"
    pub = tmp_path / "public.key"
    scroll = tmp_path / "arithmetic.moscroll"

    out = manager._moscript("keygen", "--private", str(priv), "--public", str(pub))
    assert json.loads(out)["public"] == str(pub)

    out = manager._moscript("seal", "--key", str(priv), "-o", str(scroll), str(ARITHMETIC_MS))
    assert scroll.exists()

    result = manager.execute(
        artifact_path=scroll,
        principal="tester",
        governing_contracts=["mo-mind-conduit-001"],
        governing_events={"mo-mind-conduit-001": _conduit_allow_event("tester")},
        public_key=pub,
    )

    assert result.state is RuntimeState.COMPLETED
    assert result.exit_code == 0
    assert "14" in result.stdout
    assert result.decision is not None
    assert result.decision.decision == "ALLOW"
    assert result.artifact_hash
    assert result.attestation is not None

    states = [t["state"] for t in result.transitions]
    assert states == [
        "discovered",
        "staged",
        "verified",
        "governed",
        "running",
        "completed",
    ]


def test_no_governance_is_deny(manager: RuntimeManager):
    result = manager.execute(
        artifact_path=ARITHMETIC_MS,
        principal="tester",
    )

    assert result.state is RuntimeState.DENIED
    assert result.decision is not None
    assert result.decision.decision == "DENY"
    assert "NO_GOVERNANCE" in result.decision.reason_codes


def test_capability_escalation_fails_closed(manager: RuntimeManager):
    result = manager.execute(
        artifact_path=ARITHMETIC_MS,
        principal="tester",
        governing_contracts=["mo-mind-conduit-001"],
        governing_events={"mo-mind-conduit-001": _conduit_allow_event("tester")},
        allow=["gate.execute"],  # not declared by the artifact
    )

    assert result.state is RuntimeState.FAILED
    assert "escalation" in result.stderr.lower()


def test_effective_capabilities_reach_vm(manager: RuntimeManager, monkeypatch: pytest.MonkeyPatch):
    clock_ms = FIXTURES / "clock.ms"
    run_calls: list[list[str]] = []
    original = manager._moscript

    def spy_moscript(*args: str) -> str:
        if args and args[0] == "run":
            run_calls.append(list(args))
        return original(*args)

    monkeypatch.setattr(manager, "_moscript", spy_moscript)

    result = manager.execute(
        artifact_path=clock_ms,
        principal="tester",
        governing_contracts=["mo-mind-conduit-001"],
        governing_events={"mo-mind-conduit-001": _conduit_allow_event("tester")},
    )

    assert result.state is RuntimeState.COMPLETED
    assert run_calls, "Go run must have been invoked"
    args = run_calls[0]
    assert "--allow" in args
    allow_idx = args.index("--allow")
    assert args[allow_idx + 1] == "clock.read"


def test_step_budget_exceeded(tmp_path: pathlib.Path):
    manager = RuntimeManager(
        contracts_dir=CONTRACTS_DIR,
        moscript_bin=BINARY,
        max_steps=1,
        workspace=tmp_path / "workspace",
    )
    result = manager.execute(
        artifact_path=ARITHMETIC_MS,
        principal="tester",
        governing_contracts=["mo-mind-conduit-001"],
        governing_events={"mo-mind-conduit-001": _conduit_allow_event("tester")},
    )

    assert result.state is RuntimeState.FAILED
    assert result.exit_code != 0 or "MoScript run failed" in result.stderr


def test_ms_signed_end_to_end(tmp_path: pathlib.Path):
    priv = Ed25519PrivateKey.generate()
    pub = priv.public_key()
    priv_bytes = priv.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption())
    priv_path = tmp_path / "receipt.key"
    priv_path.write_text(base64.b64encode(priv_bytes).decode("ascii"))

    manager = RuntimeManager(
        contracts_dir=CONTRACTS_DIR,
        moscript_bin=BINARY,
        workspace=tmp_path / "workspace",
        receipt_private_key=priv_path,
    )

    result = manager.execute(
        artifact_path=ARITHMETIC_MS,
        principal="tester",
        governing_contracts=["mo-mind-conduit-001"],
        governing_events={"mo-mind-conduit-001": _conduit_allow_event("tester")},
    )

    assert result.state is RuntimeState.COMPLETED
    assert result.attestation is not None
    assert result.attestation.signature
    assert result.attestation.key_id != "unsigned"
    verify_receipt(result.attestation, pub)


def test_staged_artifact_hash_matches_receipt(manager: RuntimeManager, tmp_path: pathlib.Path):
    result = manager.execute(
        artifact_path=ARITHMETIC_MS,
        principal="tester",
        governing_contracts=["mo-mind-conduit-001"],
        governing_events={"mo-mind-conduit-001": _conduit_allow_event("tester")},
        cleanup=False,
    )

    assert result.state is RuntimeState.COMPLETED
    assert result.attestation is not None
    assert result.attestation.program_hash == result.artifact_hash
    assert result.attestation.abi_hash == result.evidence["artifact"]["abi_hash"]
    staged = pathlib.Path(result.evidence["artifact"]["path"])
    assert staged.exists()
    assert result.attestation.receipt_hash == result.evidence["receipt_hash"]


def test_original_artifact_mutation_does_not_affect_staged_execution(
    manager: RuntimeManager, tmp_path: pathlib.Path
):
    # Copy the fixture to a mutable path.
    original = tmp_path / "arithmetic.ms"
    original.write_bytes(ARITHMETIC_MS.read_bytes())
    original_hash = hashlib.sha256(original.read_bytes()).hexdigest()

    result = manager.execute(
        artifact_path=original,
        principal="tester",
        governing_contracts=["mo-mind-conduit-001"],
        governing_events={"mo-mind-conduit-001": _conduit_allow_event("tester")},
        cleanup=False,
    )

    assert result.state is RuntimeState.COMPLETED
    assert "14" in result.stdout

    # Mutate the original after execution has finished.
    original.write_text("mutated", encoding="utf-8")

    # The staged, verified, and executed bytes must still be the pre-mutation bytes.
    staged = pathlib.Path(result.evidence["artifact"]["path"])
    staged_hash = hashlib.sha256(staged.read_bytes()).hexdigest()
    assert staged_hash == original_hash


def test_output_limit_exceeded(tmp_path: pathlib.Path):
    manager = RuntimeManager(
        contracts_dir=CONTRACTS_DIR,
        moscript_bin=BINARY,
        workspace=tmp_path / "workspace",
        max_output_bytes=1,
    )
    result = manager.execute(
        artifact_path=ARITHMETIC_MS,
        principal="tester",
        governing_contracts=["mo-mind-conduit-001"],
        governing_events={"mo-mind-conduit-001": _conduit_allow_event("tester")},
    )

    assert result.state is RuntimeState.FAILED
    assert result.failure is not None
    assert result.failure["reason"] == "OUTPUT_LIMIT_EXCEEDED"
    assert result.attestation is not None
    assert result.attestation.decision == "FAILED"
    assert RuntimeState.COMPLETED not in [t["state"] for t in result.transitions]


def test_external_sigkill_lands_in_failed(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch):
    real_popen = subprocess.Popen

    class KillerPopen(real_popen):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            if args and isinstance(args[0], list) and args[0] and args[0][1] in ("run", "run-scroll"):
                os.kill(self.pid, signal.SIGKILL)

    monkeypatch.setattr(subprocess, "Popen", KillerPopen)

    manager = RuntimeManager(
        contracts_dir=CONTRACTS_DIR,
        moscript_bin=BINARY,
        workspace=tmp_path / "workspace",
    )
    result = manager.execute(
        artifact_path=ARITHMETIC_MS,
        principal="tester",
        governing_contracts=["mo-mind-conduit-001"],
        governing_events={"mo-mind-conduit-001": _conduit_allow_event("tester")},
    )

    assert result.state is RuntimeState.FAILED
    assert RuntimeState.RUNNING in [t["state"] for t in result.transitions]
    assert RuntimeState.COMPLETED not in [t["state"] for t in result.transitions]
    assert result.failure is not None
    assert result.failure["phase"] == "run"
    assert result.failure["reason"] == "PROCESS_TERMINATED"
    assert result.failure["signal"] == signal.SIGKILL
    assert result.failure["signal_name"] == "SIGKILL"
    assert result.attestation is not None
    assert result.attestation.decision == "FAILED"
    assert result.attestation_id is not None


def test_replay_detected(manager: RuntimeManager):
    execution_id = str(uuid.uuid4())

    first = manager.execute(
        artifact_path=ARITHMETIC_MS,
        principal="tester",
        governing_contracts=["mo-mind-conduit-001"],
        governing_events={"mo-mind-conduit-001": _conduit_allow_event("tester")},
        execution_id=execution_id,
    )
    assert first.state is RuntimeState.COMPLETED
    assert first.attestation is not None
    assert first.attestation_id == first.attestation.attestation_id

    second = manager.execute(
        artifact_path=ARITHMETIC_MS,
        principal="tester",
        governing_contracts=["mo-mind-conduit-001"],
        governing_events={"mo-mind-conduit-001": _conduit_allow_event("tester")},
        execution_id=execution_id,
    )
    assert second.state is RuntimeState.FAILED
    assert second.failure is not None
    assert second.failure["reason"] == "REPLAY_DETECTED"
    assert second.failure["execution_id"] == execution_id
    assert second.attestation is not None
    assert second.attestation.attestation_id == first.attestation_id
