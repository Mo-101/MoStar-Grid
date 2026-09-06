"""Independent .mobc integrity verification.

Recomputes the digest the native compiler uses to seal a BytecodeFile.
The program hash cannot be recomputed from a .mobc alone because the
canonical program source is not stored in the bytecode; the .mobc can only
vouch for the bytecode hash and ABI hash it carries.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import pathlib
from dataclasses import dataclass


@dataclass(frozen=True)
class MobcIntegrity:
    valid: bool
    format: str
    program_hash_declared: str
    program_hash_computed: str | None
    bytecode_hash_declared: str
    bytecode_hash_computed: str
    abi_hash_declared: str
    abi_hash_expected: str
    capabilities: tuple[str, ...]
    errors: tuple[str, ...]


def _bytecode_digest(data: dict) -> str:
    """Recompute the native bytecode_digest over a parsed .mobc object."""
    # The native tool zeroes the bytecode_hash field before serializing.
    cp = dict(data)
    cp["bytecode_hash"] = ""
    # Match Go's json.Marshal compact output as closely as possible.
    # Preserve field order (Python 3.7+ dicts are ordered), no extra spaces,
    # no HTML escaping, None -> null, empty values as in the original object.
    payload = json.dumps(cp, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def verify_mobc(
    path: pathlib.Path,
    expected_abi_hash: str,
) -> MobcIntegrity:
    raw = path.read_bytes()
    if not raw:
        return MobcIntegrity(
            valid=False,
            format="",
            program_hash_declared="",
            program_hash_computed=None,
            bytecode_hash_declared="",
            bytecode_hash_computed="",
            abi_hash_declared="",
            abi_hash_expected=expected_abi_hash,
            capabilities=(),
            errors=("empty_mobc_file",),
        )
    try:
        data = json.loads(raw.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        return MobcIntegrity(
            valid=False,
            format="",
            program_hash_declared="",
            program_hash_computed=None,
            bytecode_hash_declared="",
            bytecode_hash_computed="",
            abi_hash_declared="",
            abi_hash_expected=expected_abi_hash,
            capabilities=(),
            errors=(f"invalid_json: {exc}",),
        )

    fmt = data.get("format", "")
    program_hash_declared = data.get("program_hash", "")
    bytecode_hash_declared = data.get("bytecode_hash", "")
    abi_hash_declared = data.get("abi_hash", "")
    capabilities = tuple(data.get("capabilities") or ())

    computed_bytecode_hash = _bytecode_digest(data)
    computed_program_hash: str | None = None  # not computable from bytecode alone

    errors: list[str] = []
    if fmt != "mobc-0.1":
        errors.append(f"unknown_format: {fmt}")
    if not hmac.compare_digest(bytecode_hash_declared, computed_bytecode_hash):
        errors.append("BYTECODE_HASH_MISMATCH")
    if abi_hash_declared and expected_abi_hash:
        if not hmac.compare_digest(abi_hash_declared, expected_abi_hash):
            errors.append("ABI_HASH_MISMATCH")
    elif expected_abi_hash and not abi_hash_declared:
        errors.append("MISSING_ABI_HASH")

    valid = not errors
    return MobcIntegrity(
        valid=valid,
        format=fmt,
        program_hash_declared=program_hash_declared,
        program_hash_computed=computed_program_hash,
        bytecode_hash_declared=bytecode_hash_declared,
        bytecode_hash_computed=computed_bytecode_hash,
        abi_hash_declared=abi_hash_declared,
        abi_hash_expected=expected_abi_hash,
        capabilities=capabilities,
        errors=tuple(errors),
    )
