"""Cryptographic helpers for scroll sealing and attestation."""
from __future__ import annotations

import base64
from typing import Any

import blake3
import jcs
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
    PublicFormat,
)


def canonical_bytes(payload: Any) -> bytes:
    """Return JSON Canonicalization Scheme bytes for a JSON-compatible payload."""
    return jcs.canonicalize(payload)


def blake3_hex(payload: bytes | str) -> str:
    if isinstance(payload, str):
        payload = payload.encode("utf-8")
    return blake3.blake3(payload).hexdigest()


def generate_ed25519_keypair() -> tuple[str, str]:
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    return (
        _b64(private_key.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption())),
        _b64(public_key.public_bytes(Encoding.Raw, PublicFormat.Raw)),
    )


def public_key_from_private_key(private_key_b64: str) -> str:
    private_key = _load_private_key(private_key_b64)
    return _b64(private_key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw))


def sign_ed25519(private_key_b64: str, payload: bytes) -> str:
    return _b64(_load_private_key(private_key_b64).sign(payload))


def verify_ed25519(public_key_b64: str, signature_b64: str, payload: bytes) -> bool:
    try:
        _load_public_key(public_key_b64).verify(_unb64(signature_b64), payload)
    except (InvalidSignature, ValueError):
        return False
    return True


def _load_private_key(private_key_b64: str) -> Ed25519PrivateKey:
    return Ed25519PrivateKey.from_private_bytes(_unb64(private_key_b64))


def _load_public_key(public_key_b64: str) -> Ed25519PublicKey:
    return Ed25519PublicKey.from_public_bytes(_unb64(public_key_b64))


def _b64(raw: bytes) -> str:
    return base64.b64encode(raw).decode("ascii")


def _unb64(encoded: str) -> bytes:
    return base64.b64decode(encoded.encode("ascii"), validate=True)
