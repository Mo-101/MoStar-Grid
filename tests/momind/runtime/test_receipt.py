"""P0 tests for canonical Ed25519 runtime receipts."""
from __future__ import annotations

import dataclasses

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from core.protocols.moscript.runtime import (
    UnsignedRuntimeReceipt,
    sign_receipt,
    verify_receipt,
)


@pytest.fixture
def keypair():
    priv = Ed25519PrivateKey.generate()
    return priv, priv.public_key()


def _sample() -> UnsignedRuntimeReceipt:
    return UnsignedRuntimeReceipt(
        schema_version=1,
        attestation_id="a" * 36,
        execution_id="b" * 36,
        issued_at="2026-01-01T00:00:00+00:00",
        runtime_id="test-runtime",
        binary_hash="0" * 64,
        program_hash="1" * 64,
        bytecode_hash="2" * 64,
        abi_hash="3" * 64,
        capabilities=("clock.read", "filesystem.read"),
        decision="ALLOW",
        result={"raw_output": "14"},
        evidence_hash="4" * 64,
        previous_receipt_hash=None,
    )


def test_sign_verify_roundtrip(keypair):
    priv, pub = keypair
    unsigned = _sample()
    receipt = sign_receipt(unsigned, priv)
    verify_receipt(receipt, pub)
    assert receipt.receipt_hash == unsigned.receipt_hash()


def test_receipt_field_mutation_breaks_signature(keypair):
    priv, pub = keypair
    receipt = sign_receipt(_sample(), priv)

    bad = dataclasses.replace(receipt, result={"raw_output": "15"})
    with pytest.raises(ValueError):
        verify_receipt(bad, pub)


def test_receipt_wrong_public_key_fails(keypair):
    priv, pub = keypair
    receipt = sign_receipt(_sample(), priv)
    other_pub = Ed25519PrivateKey.generate().public_key()
    with pytest.raises(ValueError):
        verify_receipt(receipt, other_pub)


def test_receipt_unknown_schema_fails(keypair):
    priv, pub = keypair
    unsigned = dataclasses.replace(_sample(), schema_version=99)
    receipt = sign_receipt(unsigned, priv)
    with pytest.raises(ValueError, match="schema"):
        verify_receipt(receipt, pub)


def test_receipt_truncated_signature_fails(keypair):
    priv, pub = keypair
    receipt = sign_receipt(_sample(), priv)
    truncated = receipt.signature[:-4]
    bad = dataclasses.replace(receipt, signature=truncated)
    with pytest.raises(ValueError):
        verify_receipt(bad, pub)


def test_receipt_spliced_signature_fails(keypair):
    priv, pub = keypair
    receipt1 = sign_receipt(_sample(), priv)
    other = dataclasses.replace(
        _sample(),
        attestation_id="zzzzzzzz-zzzz-zzzz-zzzz-zzzzzzzzzzzz",
        execution_id="zzzzzzzz-zzzz-zzzz-zzzz-zzzzzzzzzzzz",
    )
    receipt2 = sign_receipt(other, priv)
    # Lift a valid signature from a different receipt.
    spliced = dataclasses.replace(receipt2, signature=receipt1.signature)
    with pytest.raises(ValueError):
        verify_receipt(spliced, pub)
