"""Scroll envelope model for Phase 3 federation."""
from __future__ import annotations

import secrets
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from grid.config import (
    MOSTAR_CLUSTER_ID,
    MOSTAR_CLUSTER_REGION,
)

from federation.crypto import blake3_hex, canonical_bytes, sign_ed25519, verify_ed25519


SCROLL_VERSION = "1.0.0"
SCHEMA_VERSION = "4.0a"
SEAL_ALGORITHM = "blake3"
SIGNATURE_ALGORITHM = "ed25519"


@dataclass
class ScrollCluster:
    cluster_id: str
    cluster_pubkey: str
    cluster_region: str


@dataclass
class ScrollAction:
    action_type: str
    intent: str
    risk_level: str = "low"
    reversibility: str = "partial"


@dataclass
class ScrollParticipants:
    requester_soulprint_hash: str
    approver_hashes: list[str] = field(default_factory=list)
    witness_hashes: list[str] = field(default_factory=list)


@dataclass
class ScrollEvidence:
    evidence_hashes: list[str] = field(default_factory=list)
    evidence_access: str = "on_request"
    proof_of_arrival_required: bool = False


@dataclass
class ScrollSeal:
    seal_algorithm: str = SEAL_ALGORITHM
    seal_hash: str = ""
    signature_algorithm: str = SIGNATURE_ALGORITHM
    cluster_signatures: list[str] = field(default_factory=list)


@dataclass
class ScrollLifecycle:
    status: str = "sealed"
    created_at: str = ""
    expires_at: str | None = None
    revoked: bool = False
    revocation_reason: str | None = None


@dataclass
class Scroll:
    scroll_version: str
    scroll_id: str
    schema_version: str
    cluster: ScrollCluster
    action: ScrollAction
    participants: ScrollParticipants
    inputs: dict[str, Any]
    gate_receipts: dict[str, Any]
    evidence: ScrollEvidence
    human_context: dict[str, Any]
    attestations: list[dict[str, Any]]
    seal: ScrollSeal
    lifecycle: ScrollLifecycle

    @classmethod
    def create(
        cls,
        *,
        cluster_pubkey: str,
        action: ScrollAction,
        participants: ScrollParticipants,
        inputs: dict[str, Any],
        gate_receipts: dict[str, Any],
        evidence: ScrollEvidence | None = None,
        human_context: dict[str, Any] | None = None,
        cluster_id: str = MOSTAR_CLUSTER_ID,
        cluster_region: str = MOSTAR_CLUSTER_REGION,
        created_at: str | None = None,
    ) -> "Scroll":
        created_at = created_at or _now()
        return cls(
            scroll_version=SCROLL_VERSION,
            scroll_id=f"scr-{cluster_id}-{_compact_timestamp(created_at)}-{secrets.token_hex(6)}",
            schema_version=SCHEMA_VERSION,
            cluster=ScrollCluster(
                cluster_id=cluster_id,
                cluster_pubkey=cluster_pubkey,
                cluster_region=cluster_region,
            ),
            action=action,
            participants=participants,
            inputs=inputs,
            gate_receipts=gate_receipts,
            evidence=evidence or ScrollEvidence(),
            human_context=human_context or {},
            attestations=[],
            seal=ScrollSeal(),
            lifecycle=ScrollLifecycle(created_at=created_at),
        )

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "Scroll":
        return cls(
            scroll_version=payload["scroll_version"],
            scroll_id=payload["scroll_id"],
            schema_version=payload["schema_version"],
            cluster=ScrollCluster(**payload["cluster"]),
            action=ScrollAction(**payload["action"]),
            participants=ScrollParticipants(**payload["participants"]),
            inputs=payload["inputs"],
            gate_receipts=payload["gate_receipts"],
            evidence=ScrollEvidence(**payload["evidence"]),
            human_context=payload["human_context"],
            attestations=payload.get("attestations", []),
            seal=ScrollSeal(**payload["seal"]),
            lifecycle=ScrollLifecycle(**payload["lifecycle"]),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def unsigned_payload(self) -> dict[str, Any]:
        payload = self.to_dict()
        payload["attestations"] = []
        payload["seal"]["seal_hash"] = ""
        payload["seal"]["cluster_signatures"] = []
        return payload

    def canonical_unsigned_bytes(self) -> bytes:
        return canonical_bytes(self.unsigned_payload())

    def seal_hash(self) -> str:
        return blake3_hex(self.canonical_unsigned_bytes())

    def seal_with_cluster_key(self, private_key_b64: str) -> "Scroll":
        seal_hash = self.seal_hash()
        signature = sign_ed25519(private_key_b64, seal_hash.encode("ascii"))
        self.seal = ScrollSeal(
            seal_hash=seal_hash,
            cluster_signatures=[signature],
        )
        return self

    def add_cluster_signature(self, private_key_b64: str) -> "Scroll":
        if not self.seal.seal_hash:
            self.seal.seal_hash = self.seal_hash()
        if self.seal.seal_hash != self.seal_hash():
            raise ValueError("Cannot sign a scroll whose payload no longer matches its seal hash")
        self.seal.cluster_signatures.append(
            sign_ed25519(private_key_b64, self.seal.seal_hash.encode("ascii"))
        )
        return self

    def verify_cluster_signature(self) -> bool:
        return self.verify_cluster_signatures(min_signatures=1)

    def verify_cluster_signatures(self, min_signatures: int = 1) -> bool:
        if not self.seal.seal_hash or not self.seal.cluster_signatures:
            return False
        if len(self.seal.cluster_signatures) < min_signatures:
            return False
        if self.seal.seal_hash != self.seal_hash():
            return False
        return all(
            verify_ed25519(
                self.cluster.cluster_pubkey,
                signature,
                self.seal.seal_hash.encode("ascii"),
            )
            for signature in self.seal.cluster_signatures
        )

    def revoke(self, reason: str) -> "Scroll":
        self.lifecycle.status = "revoked"
        self.lifecycle.revoked = True
        self.lifecycle.revocation_reason = reason
        return self

    def append_attestation(self, attestation: dict[str, Any]) -> "Scroll":
        self.attestations.append(attestation)
        return self


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _compact_timestamp(timestamp: str) -> str:
    return (
        timestamp.replace(":", "")
        .replace("-", "")
        .replace(".", "")
        .replace("+", "")
        .replace("Z", "Z")
    )
