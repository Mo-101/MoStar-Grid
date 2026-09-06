"""P0 tests for .mobc integrity verification."""
from __future__ import annotations

import json
import pathlib
import subprocess

import pytest

from core.protocols.moscript.runtime import verify_mobc


PROJECT_ROOT = pathlib.Path(__file__).parent.parent.parent.parent.resolve()
BINARY = PROJECT_ROOT / "core" / "protocols" / "moscript" / "moscript-v0.1.1-linux-amd64"
ARITHMETIC_MS = (
    pathlib.Path(__file__).parent / "fixtures" / "arithmetic.ms"
)


def _moscript(*args) -> str:
    proc = subprocess.run(
        [str(BINARY), *args],
        capture_output=True,
        text=True,
        check=True,
    )
    return proc.stdout


def _abi_hash() -> str:
    out = _moscript("abi")
    return json.loads(out)["abi_hash"]


def _compile(tmp_path: pathlib.Path) -> pathlib.Path:
    mobc = tmp_path / "arithmetic.mobc"
    _moscript("compile", "-o", str(mobc), str(ARITHMETIC_MS))
    return mobc


def test_mobc_integrity_matches_native_compilation(tmp_path: pathlib.Path):
    mobc = _compile(tmp_path)
    integrity = verify_mobc(mobc, _abi_hash())
    assert integrity.valid, integrity.errors
    assert integrity.bytecode_hash_declared == integrity.bytecode_hash_computed


def test_mobc_bytecode_hash_mismatch_fails(tmp_path: pathlib.Path):
    mobc = _compile(tmp_path)
    data = json.loads(mobc.read_text(encoding="utf-8"))
    # Tamper with a single instruction opcode.
    data["main"]["code"][0]["op"] = "HALT"
    mobc.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")

    integrity = verify_mobc(mobc, _abi_hash())
    assert not integrity.valid
    assert "BYTECODE_HASH_MISMATCH" in integrity.errors
