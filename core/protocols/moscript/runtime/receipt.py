"""Canonical, Ed25519-signed MoScript runtime receipts.

Implements JCS (RFC 8785) canonicalization for the unsigned payload, then signs
DOMAIN || canonical_bytes with Ed25519. The signature is not included in the
bytes being signed.
"""
from __future__ import annotations

import base64
import hashlib
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

import jcs
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.exceptions import InvalidSignature


RECEIPT_DOMAIN = b"moscript-runtime-receipt:v1\x00"


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _from_b64url(text: str) -> bytes:
    pad = "=" * ((4 - len(text) % 4) % 4)
    return base64.urlsafe_b64decode(text + pad)


def _key_id(public_key: Ed25519PublicKey) -> str:
    """Stable key identifier from the raw public key bytes."""
    return hashlib.sha256(public_key.public_bytes_raw()).hexdigest()[:32]


@dataclass(frozen=True)
class UnsignedRuntimeReceipt:
    """The signed body of a runtime receipt."""

    schema_version: int
    attestation_id: str
    execution_id: str
    issued_at: str
    runtime_id: str
    binary_hash: str
    program_hash: str
    bytecode_hash: str
    abi_hash: str
    capabilities: tuple[str, ...]
    decision: str
    result: dict[str, Any] = field(default_factory=dict)
    evidence_hash: str = ""
    previous_receipt_hash: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def canonical_bytes(self) -> bytes:
        return jcs.canonicalize(self.to_dict())

    def signed_input(self) -> bytes:
        return RECEIPT_DOMAIN + self.canonical_bytes()

    def receipt_hash(self) -> str:
        return hashlib.sha256(self.signed_input()).hexdigest()


@dataclass(frozen=True)
class RuntimeReceipt:
    """A completed, signed runtime receipt ready for storage."""

    schema_version: int
    attestation_id: str
    execution_id: str
    issued_at: str
    runtime_id: str
    binary_hash: str
    program_hash: str
    bytecode_hash: str
    abi_hash: str
    capabilities: tuple[str, ...]
    decision: str
    result: dict[str, Any] = field(default_factory=dict)
    evidence_hash: str = ""
    previous_receipt_hash: str | None = None
    receipt_hash: str = ""
    signature: str = ""
    signature_algorithm: str = "Ed25519"
    key_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def unsigned(self) -> UnsignedRuntimeReceipt:
        return UnsignedRuntimeReceipt(
            schema_version=self.schema_version,
            attestation_id=self.attestation_id,
            execution_id=self.execution_id,
            issued_at=self.issued_at,
            runtime_id=self.runtime_id,
            binary_hash=self.binary_hash,
            program_hash=self.program_hash,
            bytecode_hash=self.bytecode_hash,
            abi_hash=self.abi_hash,
            capabilities=self.capabilities,
            decision=self.decision,
            result=self.result,
            evidence_hash=self.evidence_hash,
            previous_receipt_hash=self.previous_receipt_hash,
        )


def sign_receipt(
    unsigned: UnsignedRuntimeReceipt,
    private_key: Ed25519PrivateKey,
    public_key: Ed25519PublicKey | None = None,
) -> RuntimeReceipt:
    """Sign an unsigned receipt and produce a completed receipt."""
    signed_input = unsigned.signed_input()
    signature = private_key.sign(signed_input)
    pub = public_key if public_key is not None else private_key.public_key()
    return RuntimeReceipt(
        **asdict(unsigned),
        receipt_hash=hashlib.sha256(signed_input).hexdigest(),
        signature=_b64url(signature),
        signature_algorithm="Ed25519",
        key_id=_key_id(pub),
    )


def verify_receipt(
    receipt: RuntimeReceipt,
    public_key: Ed25519PublicKey,
) -> None:
    """Verify a completed receipt. Raises on any failure, fail-closed."""
    if receipt.schema_version != 1:
        raise ValueError(f"unsupported schema version: {receipt.schema_version}")
    if receipt.signature_algorithm != "Ed25519":
        raise ValueError(f"unsupported algorithm: {receipt.signature_algorithm}")
    if receipt.key_id != _key_id(public_key):
        raise ValueError("public key does not match receipt key_id")
    unsigned = receipt.unsigned
    expected_hash = unsigned.receipt_hash()
    if receipt.receipt_hash != expected_hash:
        raise ValueError("receipt_hash does not match canonical unsigned payload")
    try:
        signature_bytes = _from_b64url(receipt.signature)
    except Exception as exc:
        raise ValueError("malformed signature encoding") from exc
    try:
        public_key.verify(signature_bytes, unsigned.signed_input())
    except InvalidSignature as exc:
        raise ValueError("signature verification failed") from exc


def validate_receipt_dict(data: dict[str, Any]) -> RuntimeReceipt:
    """Parse and fail-closed-validate a receipt dictionary."""
    required = {
        "schema_version",
        "attestation_id",
        "execution_id",
        "issued_at",
        "runtime_id",
        "binary_hash",
        "program_hash",
        "bytecode_hash",
        "abi_hash",
        "capabilities",
        "decision",
        "receipt_hash",
        "signature",
        "signature_algorithm",
        "key_id",
    }
    missing = required - set(data)
    if missing:
        raise ValueError(f"missing receipt fields: {sorted(missing)}")
    return RuntimeReceipt(**data)
