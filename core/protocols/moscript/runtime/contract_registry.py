"""Immutable, hash-sealed, schema-validated contract registry."""
from __future__ import annotations

import hashlib
import json
import pathlib
from dataclasses import dataclass
from typing import Any

import jsonschema

from .contract_decision import GovernanceFailure


@dataclass(frozen=True)
class SealedContract:
    id: str
    name: str
    trigger: str
    inputs: tuple[str, ...]
    law: str
    required_result: str
    file: str
    sha256: str
    raw: dict[str, Any]


class ContractRegistry:
    """Load contracts from a manifest, verify hashes, validate schema, freeze."""

    def __init__(self):
        self._contracts: dict[str, SealedContract] = {}
        self._ready = False
        self._schema: dict[str, Any] | None = None

    @classmethod
    def from_path(cls, contracts_dir: pathlib.Path | str) -> "ContractRegistry":
        inst = cls()
        inst.load_and_freeze(pathlib.Path(contracts_dir))
        return inst

    def load_and_freeze(self, contracts_dir: pathlib.Path):
        contracts_dir = pathlib.Path(contracts_dir)
        schema_path = contracts_dir / "contract.schema.json"
        manifest_path = contracts_dir / "contracts.manifest.json"

        self._schema = json.loads(schema_path.read_text(encoding="utf-8"))
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        ids = set()
        for entry in manifest.get("contracts", []):
            cid = entry["id"]
            if cid in ids:
                raise GovernanceFailure(f"duplicate contract id {cid}")
            ids.add(cid)

            file_path = contracts_dir / entry["file"]
            raw_bytes = file_path.read_bytes()
            actual_hash = hashlib.sha256(raw_bytes).hexdigest()
            if actual_hash != entry["sha256"]:
                raise GovernanceFailure(
                    f"hash mismatch for {cid}: expected {entry['sha256']}, got {actual_hash}"
                )

            data = json.loads(raw_bytes.decode("utf-8"))
            try:
                jsonschema.validate(data, self._schema)
            except jsonschema.ValidationError as e:
                raise GovernanceFailure(f"schema validation failed for {cid}: {e.message}") from e

            if data["id"] != cid:
                raise GovernanceFailure(
                    f"manifest id {cid} does not match contract id {data['id']}"
                )

            self._contracts[cid] = SealedContract(
                id=data["id"],
                name=data["name"],
                trigger=data["trigger"],
                inputs=tuple(data["inputs"]),
                law=data["law"],
                required_result=data["required_result"],
                file=entry["file"],
                sha256=actual_hash,
                raw=data,
            )

        self._ready = True

    @property
    def ready(self) -> bool:
        return self._ready

    def get(self, contract_id: str) -> SealedContract:
        if not self._ready:
            raise GovernanceFailure("contract registry has not been frozen")
        if contract_id not in self._contracts:
            raise GovernanceFailure(f"unknown contract {contract_id}")
        return self._contracts[contract_id]

    def __contains__(self, contract_id: str) -> bool:
        return contract_id in self._contracts

    def ids(self) -> list[str]:
        if not self._ready:
            raise GovernanceFailure("contract registry has not been frozen")
        return list(self._contracts.keys())
