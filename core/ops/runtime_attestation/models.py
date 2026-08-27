"""Data models for runtime attestation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RuntimeManifest:
    schema_version: str
    system_id: str
    runtime_id: str
    runtime_version: str
    build_commit: str
    build_timestamp: str
    runtime_digest: str
    components: dict[str, str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "system_id": self.system_id,
            "runtime_id": self.runtime_id,
            "runtime_version": self.runtime_version,
            "build_commit": self.build_commit,
            "build_timestamp": self.build_timestamp,
            "runtime_digest": self.runtime_digest,
            "components": self.components,
        }


@dataclass(frozen=True)
class RuntimeIdentity:
    system_id: str
    runtime_id: str
    runtime_version: str
    build_commit: str
    runtime_digest: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "system_id": self.system_id,
            "runtime_id": self.runtime_id,
            "runtime_version": self.runtime_version,
            "build_commit": self.build_commit,
            "runtime_digest": self.runtime_digest,
        }


@dataclass(frozen=True)
class GridReadiness:
    ready: bool
    runtime_verified: bool
    seal_verified: bool
    attestation_id: str | None
    failures: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "ready": self.ready,
            "runtime_verified": self.runtime_verified,
            "seal_verified": self.seal_verified,
            "attestation_id": self.attestation_id,
            "failures": self.failures,
        }
