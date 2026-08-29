"""Sealed manifest and integrity tests."""
from __future__ import annotations

import hashlib
import json
import pathlib
import shutil

import pytest

from moscript.runtime.contract_registry import ContractRegistry, GovernanceFailure

CONTRACTS_DIR = pathlib.Path("core/protocols/moscript/contracts")


def test_manifest_hashes_match():
    registry = ContractRegistry.from_path(CONTRACTS_DIR)
    for cid in registry.ids():
        contract = registry.get(cid)
        expected = hashlib.sha256(
            (CONTRACTS_DIR / contract.file).read_bytes()
        ).hexdigest()
        assert contract.sha256 == expected


def test_one_byte_tamper_fails(tmp_path):
    dst = tmp_path / "contracts"
    shutil.copytree(CONTRACTS_DIR, dst)
    file_path = dst / "mo-mind-attestation-guard-001.json"
    file_path.write_text(file_path.read_text() + " ")
    with pytest.raises(GovernanceFailure):
        ContractRegistry().load_and_freeze(dst)


def test_duplicate_contract_id_fails(tmp_path):
    dst = tmp_path / "contracts"
    shutil.copytree(CONTRACTS_DIR, dst)
    manifest = json.loads((dst / "contracts.manifest.json").read_text())
    manifest["contracts"].append(manifest["contracts"][0])
    (dst / "contracts.manifest.json").write_text(json.dumps(manifest, indent=2))
    with pytest.raises(GovernanceFailure):
        ContractRegistry().load_and_freeze(dst)


def test_unknown_contract_fails_closed():
    registry = ContractRegistry.from_path(CONTRACTS_DIR)
    with pytest.raises(GovernanceFailure):
        registry.get("mo-mind-does-not-exist-001")
