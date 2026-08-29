"""JSON Schema envelope validation for the four contracts."""
from __future__ import annotations

import hashlib
import json
import pathlib
import shutil

import jsonschema
import pytest

from moscript.runtime.contract_registry import ContractRegistry, GovernanceFailure

CONTRACTS_DIR = pathlib.Path("core/protocols/moscript/contracts")


def _load_schema() -> dict:
    return json.loads((CONTRACTS_DIR / "contract.schema.json").read_text())


def test_all_contracts_validate():
    registry = ContractRegistry.from_path(CONTRACTS_DIR)
    assert registry.ready
    assert set(registry.ids()) == {
        "mo-mind-attestation-guard-001",
        "mo-mind-conduit-001",
        "mo-mind-cypher-guard-001",
        "mo-mind-provenance-filter-001",
    }


def test_schema_rejects_extra_property():
    schema = _load_schema()
    good = {
        "id": "mo-mind-test-001",
        "name": "Test",
        "trigger": "on_test",
        "inputs": ["x"],
        "law": "test law",
        "required_result": "ALLOW",
    }
    jsonschema.validate(good, schema)
    bad = {**good, "extra": "field"}
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, schema)


def test_schema_rejects_bad_id():
    schema = _load_schema()
    bad = {
        "id": "not-mind-001",
        "name": "Test",
        "trigger": "on_test",
        "inputs": ["x"],
        "law": "test law",
        "required_result": "ALLOW",
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, schema)


def test_malformed_law_fails(tmp_path):
    dst = tmp_path / "contracts"
    shutil.copytree(CONTRACTS_DIR, dst)
    file_path = dst / "mo-mind-attestation-guard-001.json"
    data = json.loads(file_path.read_text())
    data["law"] = 123
    file_path.write_text(json.dumps(data))

    manifest = json.loads((dst / "contracts.manifest.json").read_text())
    new_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
    for entry in manifest["contracts"]:
        if entry["id"] == data["id"]:
            entry["sha256"] = new_hash
    (dst / "contracts.manifest.json").write_text(json.dumps(manifest, indent=2))

    with pytest.raises(GovernanceFailure):
        ContractRegistry().load_and_freeze(dst)
