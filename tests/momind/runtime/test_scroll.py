"""Negative tests for the .moscroll execution seal."""
from __future__ import annotations

import base64
import json
import pathlib
import subprocess

import pytest

from core.protocols.moscript.runtime import RuntimeManager, RuntimeState


PROJECT_ROOT = pathlib.Path(__file__).parent.parent.parent.parent.resolve()
CONTRACTS_DIR = PROJECT_ROOT / "core" / "protocols" / "moscript" / "contracts"
BINARY = PROJECT_ROOT / "core" / "protocols" / "moscript" / "moscript-v0.1.1-linux-amd64"
ARITHMETIC_MS = pathlib.Path(__file__).parent / "fixtures" / "arithmetic.ms"


def _manager(tmp_path: pathlib.Path) -> RuntimeManager:
    return RuntimeManager(
        contracts_dir=CONTRACTS_DIR,
        moscript_bin=BINARY,
        workspace=tmp_path / "workspace",
    )


def _seal(tmp_path: pathlib.Path, manager: RuntimeManager) -> tuple[pathlib.Path, pathlib.Path, pathlib.Path]:
    priv = tmp_path / "private.key"
    pub = tmp_path / "public.key"
    scroll = tmp_path / "arithmetic.moscroll"
    manager._moscript("keygen", "--private", str(priv), "--public", str(pub))
    manager._moscript("seal", "--key", str(priv), "-o", str(scroll), str(ARITHMETIC_MS))
    return priv, pub, scroll


def _conduit_allow_event(principal: str) -> dict:
    return {
        "binding": {"sealed": True},
        "authority": {"approved": True},
        "caller": principal,
        "model_runtime": "local",
    }


def test_moscroll_allow_end_to_end(tmp_path: pathlib.Path):
    manager = _manager(tmp_path)
    _priv, pub, scroll = _seal(tmp_path, manager)

    result = manager.execute(
        artifact_path=scroll,
        principal="tester",
        governing_contracts=["mo-mind-conduit-001"],
        governing_events={"mo-mind-conduit-001": _conduit_allow_event("tester")},
        public_key=pub,
    )

    assert result.state is RuntimeState.COMPLETED
    assert "14" in result.stdout


def test_scroll_payload_mutation_breaks_signature(tmp_path: pathlib.Path):
    manager = _manager(tmp_path)
    _priv, pub, scroll = _seal(tmp_path, manager)

    raw = json.loads(scroll.read_text(encoding="utf-8"))
    # Mutate the program hash claim; the signature is over the original payload.
    raw["program_hash"] = "0" * 64
    scroll.write_text(json.dumps(raw, separators=(",", ":")), encoding="utf-8")

    result = manager.execute(
        artifact_path=scroll,
        principal="tester",
        governing_contracts=["mo-mind-conduit-001"],
        governing_events={"mo-mind-conduit-001": _conduit_allow_event("tester")},
        public_key=pub,
    )

    assert result.state is RuntimeState.FAILED


def test_scroll_truncated_signature_fails(tmp_path: pathlib.Path):
    manager = _manager(tmp_path)
    _priv, pub, scroll = _seal(tmp_path, manager)

    raw = json.loads(scroll.read_text(encoding="utf-8"))
    raw["signature"] = raw["signature"][:-4]
    scroll.write_text(json.dumps(raw, separators=(",", ":")), encoding="utf-8")

    result = manager.execute(
        artifact_path=scroll,
        principal="tester",
        governing_contracts=["mo-mind-conduit-001"],
        governing_events={"mo-mind-conduit-001": _conduit_allow_event("tester")},
        public_key=pub,
    )

    assert result.state is RuntimeState.FAILED


def test_scroll_spliced_signature_fails(tmp_path: pathlib.Path):
    manager = _manager(tmp_path)
    _priv, pub, scroll_a = _seal(tmp_path, manager)

    # Seal a second scroll with the SAME trusted key.
    scroll_b = tmp_path / "arithmetic_b.moscroll"
    manager._moscript("seal", "--key", str(_priv), "-o", str(scroll_b), str(ARITHMETIC_MS))

    raw_b = json.loads(scroll_b.read_text(encoding="utf-8"))
    raw_a = json.loads(scroll_a.read_text(encoding="utf-8"))
    raw_b["signature"] = raw_a["signature"]
    scroll_b.write_text(json.dumps(raw_b, separators=(",", ":")), encoding="utf-8")

    result = manager.execute(
        artifact_path=scroll_b,
        principal="tester",
        governing_contracts=["mo-mind-conduit-001"],
        governing_events={"mo-mind-conduit-001": _conduit_allow_event("tester")},
        public_key=pub,
    )

    assert result.state is RuntimeState.FAILED


def test_moscroll_verified_bytes_are_attested_bytes(tmp_path: pathlib.Path):
    manager = _manager(tmp_path)
    _priv, pub, scroll = _seal(tmp_path, manager)

    result = manager.execute(
        artifact_path=scroll,
        principal="tester",
        governing_contracts=["mo-mind-conduit-001"],
        governing_events={"mo-mind-conduit-001": _conduit_allow_event("tester")},
        public_key=pub,
        cleanup=False,
    )

    assert result.state is RuntimeState.COMPLETED
    staged = pathlib.Path(result.evidence["artifact"]["path"])
    assert staged.exists()

    # The program_hash attested in the receipt must match the one the Go
    # runtime reports when it independently verifies the exact staged bytes.
    verify_out = manager._moscript("verify", "--pub", str(pub), str(staged))
    verify_data = json.loads(verify_out)
    assert verify_data["program_hash"] == result.artifact_hash
    assert verify_data["program_hash"] == result.attestation.program_hash


def test_moscroll_popen_path_identity(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
):
    manager = _manager(tmp_path)
    _priv, pub, scroll = _seal(tmp_path, manager)

    calls: list[list[str]] = []
    real_popen = subprocess.Popen

    class SpyPopen(real_popen):
        def __init__(self, *args, **kwargs):
            if args and isinstance(args[0], list):
                calls.append(list(args[0]))
            super().__init__(*args, **kwargs)

    monkeypatch.setattr(subprocess, "Popen", SpyPopen)

    result = manager.execute(
        artifact_path=scroll,
        principal="tester",
        governing_contracts=["mo-mind-conduit-001"],
        governing_events={"mo-mind-conduit-001": _conduit_allow_event("tester")},
        public_key=pub,
        cleanup=False,
    )

    assert result.state is RuntimeState.COMPLETED
    verify_paths = [c[-1] for c in calls if "verify" in c]
    run_paths = [c[-1] for c in calls if "run-scroll" in c]
    assert len(verify_paths) == 1
    assert len(run_paths) == 1
    assert verify_paths[0] == run_paths[0]
    assert verify_paths[0].endswith(".moscroll")
    assert pathlib.Path(verify_paths[0]).exists()
