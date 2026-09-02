"""Append-only, tamper-evident provenance storage for runtime receipts.

Primary storage is PostgreSQL. When the database is unavailable, receipts are
spooled to an append-only local file and can be replayed later without
re-signing.

The chain head is locked during issuance so the previous hash is authoritative
at the moment the receipt is signed.
"""
from __future__ import annotations

import json
import os
import pathlib
import socket
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .receipt import RuntimeReceipt, validate_receipt_dict, verify_receipt


@dataclass
class ProvenanceResult:
    stored: bool
    stored_at: str
    backend: str
    receipt: RuntimeReceipt | None = None
    error: str | None = None


@dataclass
class ChainResult:
    valid: bool
    checked: int
    first_invalid_index: int | None = None
    first_invalid_reason: str | None = None


class ProvenanceStore:
    """Store signed receipts in PostgreSQL and/or a local append-only spool."""

    def __init__(
        self,
        *,
        runtime_id: str,
        database_url: str | None = None,
        spool_dir: pathlib.Path | str | None = None,
    ):
        self.runtime_id = runtime_id
        self.database_url = database_url
        self.spool_dir = pathlib.Path(
            spool_dir
            if spool_dir is not None
            else pathlib.Path.home() / ".config" / "grid" / "provenance"
        )
        self._engine = None
        if self.database_url:
            try:
                from sqlalchemy import create_engine

                self._engine = create_engine(
                    self.database_url,
                    pool_pre_ping=True,
                    future=True,
                )
            except Exception:
                self._engine = None

    @classmethod
    def from_env(cls, spool_dir: pathlib.Path | str | None = None) -> "ProvenanceStore":
        runtime_id = os.environ.get("MOSCRIPT_RUNTIME_ID", socket.gethostname())
        database_url = os.environ.get("DATABASE_URL")
        return cls(
            runtime_id=runtime_id,
            database_url=database_url,
            spool_dir=spool_dir,
        )

    def ensure_tables(self) -> None:
        if not self._engine:
            return
        from sqlalchemy import text

        with self._engine.begin() as conn:
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS provenance"))
            conn.execute(text(
                "CREATE TABLE IF NOT EXISTS provenance.moscript_receipts "
                "(attestation_id UUID PRIMARY KEY, execution_id UUID NOT NULL, "
                "runtime_id TEXT NOT NULL, sequence_no BIGINT NOT NULL, "
                "previous_receipt_hash TEXT, receipt_hash TEXT NOT NULL UNIQUE, "
                "key_id TEXT NOT NULL, signature_algorithm TEXT NOT NULL, "
                "signature TEXT NOT NULL, receipt JSONB NOT NULL, "
                "created_at TIMESTAMPTZ NOT NULL DEFAULT now(), "
                "UNIQUE(runtime_id, sequence_no))"
            ))
            conn.execute(text(
                "CREATE TABLE IF NOT EXISTS provenance.moscript_chain_heads "
                "(runtime_id TEXT PRIMARY KEY, sequence_no BIGINT NOT NULL, "
                "receipt_hash TEXT NOT NULL, updated_at TIMESTAMPTZ NOT NULL DEFAULT now())"
            ))

    def _spool_path(self) -> pathlib.Path:
        self.spool_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        return self.spool_dir / f"{self.runtime_id}_receipts.jsonl"

    def _append_local(self, receipt: RuntimeReceipt) -> None:
        path = self._spool_path()
        record = {
            "attestation_id": receipt.attestation_id,
            "runtime_id": receipt.runtime_id,
            "receipt_hash": receipt.receipt_hash,
            "previous_receipt_hash": receipt.previous_receipt_hash,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "receipt": receipt.to_dict(),
        }
        data = (json.dumps(record, sort_keys=True) + "\n").encode("utf-8")
        flags = (
            os.O_WRONLY
            | os.O_CREAT
            | os.O_APPEND
            | os.O_CLOEXEC
            | os.O_NOFOLLOW
        )
        fd = os.open(path, flags, 0o600)
        try:
            os.write(fd, data)
            os.fsync(fd)
        finally:
            os.close(fd)

    def _local_head(self) -> tuple[int, str | None]:
        path = self._spool_path()
        if not path.exists():
            return 0, None
        try:
            with open(path, "r", encoding="utf-8") as f:
                last = None
                for line in f:
                    if line.strip():
                        last = json.loads(line)
                if last is None:
                    return 0, None
                return last.get("sequence_no", 0), last.get("receipt_hash")
        except Exception:
            return 0, None

    def _set_local_head(self, receipt: RuntimeReceipt, sequence_no: int) -> None:
        path = self._spool_path()
        record = {
            "attestation_id": receipt.attestation_id,
            "runtime_id": receipt.runtime_id,
            "receipt_hash": receipt.receipt_hash,
            "previous_receipt_hash": receipt.previous_receipt_hash,
            "sequence_no": sequence_no,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "receipt": receipt.to_dict(),
        }
        data = (json.dumps(record, sort_keys=True) + "\n").encode("utf-8")
        flags = (
            os.O_WRONLY
            | os.O_CREAT
            | os.O_APPEND
            | os.O_CLOEXEC
            | os.O_NOFOLLOW
        )
        fd = os.open(path, flags, 0o600)
        try:
            os.write(fd, data)
            os.fsync(fd)
        finally:
            os.close(fd)

    def record_receipt_builder(
        self,
        builder: Callable[[str | None], RuntimeReceipt],
    ) -> ProvenanceResult:
        """Issue a receipt with an authoritative chain head.

        `builder(previous_receipt_hash)` is called while the chain head is
        locked so the receipt is signed against the exact head at commit time.
        """
        if not self._engine:
            seq, previous_hash = self._local_head()
            receipt = builder(previous_hash)
            self._set_local_head(receipt, seq + 1)
            return ProvenanceResult(
                stored=True,
                stored_at=datetime.now(timezone.utc).isoformat(),
                backend="local_spool",
                receipt=receipt,
            )

        try:
            from sqlalchemy import text

            self.ensure_tables()
            with self._engine.begin() as conn:
                # Lock the chain head before choosing the previous hash.
                conn.execute(
                    text(
                        "INSERT INTO provenance.moscript_chain_heads "
                        "(runtime_id, sequence_no, receipt_hash, updated_at) "
                        "VALUES (:runtime_id, 0, '', now()) "
                        "ON CONFLICT (runtime_id) DO NOTHING"
                    ),
                    {"runtime_id": self.runtime_id},
                )
                row = conn.execute(
                    text(
                        "SELECT sequence_no, receipt_hash "
                        "FROM provenance.moscript_chain_heads "
                        "WHERE runtime_id = :runtime_id "
                        "FOR UPDATE"
                    ),
                    {"runtime_id": self.runtime_id},
                ).mappings().one()
                previous_hash = row["receipt_hash"] if row["receipt_hash"] else None

                receipt = builder(previous_hash)

                # Idempotent insertion with attestation-id collision guard.
                conn.execute(
                    text(
                        "INSERT INTO provenance.moscript_receipts "
                        "(attestation_id, execution_id, runtime_id, sequence_no, "
                        "previous_receipt_hash, receipt_hash, key_id, "
                        "signature_algorithm, signature, receipt, created_at) "
                        "VALUES (:attestation_id, :execution_id, :runtime_id, "
                        ":sequence_no, :previous_receipt_hash, :receipt_hash, :key_id, "
                        ":signature_algorithm, :signature, :receipt, now()) "
                        "ON CONFLICT (attestation_id) DO NOTHING"
                    ),
                    {
                        "attestation_id": receipt.attestation_id,
                        "execution_id": receipt.execution_id,
                        "runtime_id": receipt.runtime_id,
                        "sequence_no": row["sequence_no"] + 1,
                        "previous_receipt_hash": receipt.previous_receipt_hash,
                        "receipt_hash": receipt.receipt_hash,
                        "key_id": receipt.key_id,
                        "signature_algorithm": receipt.signature_algorithm,
                        "signature": receipt.signature,
                        "receipt": json.dumps(receipt.to_dict()),
                    },
                )

                # Verify the insert succeeded and no hash collision.
                existing = conn.execute(
                    text(
                        "SELECT receipt_hash, sequence_no FROM provenance.moscript_receipts "
                        "WHERE attestation_id = :attestation_id"
                    ),
                    {"attestation_id": receipt.attestation_id},
                ).mappings().one()
                if existing["receipt_hash"] != receipt.receipt_hash:
                    raise RuntimeError("ATTESTATION_ID_COLLISION")

                conn.execute(
                    text(
                        "UPDATE provenance.moscript_chain_heads "
                        "SET sequence_no = :sequence_no, "
                        "receipt_hash = :receipt_hash, "
                        "updated_at = now() "
                        "WHERE runtime_id = :runtime_id"
                    ),
                    {
                        "runtime_id": self.runtime_id,
                        "sequence_no": existing["sequence_no"],
                        "receipt_hash": receipt.receipt_hash,
                    },
                )

            # Best-effort local spool as well.
            self._append_local(receipt)

            return ProvenanceResult(
                stored=True,
                stored_at=datetime.now(timezone.utc).isoformat(),
                backend="postgresql",
                receipt=receipt,
            )
        except Exception as exc:
            # Fall back to local spool rather than lose evidence.
            seq, previous_hash = self._local_head()
            receipt = builder(previous_hash)
            self._set_local_head(receipt, seq + 1)
            return ProvenanceResult(
                stored=True,
                stored_at=datetime.now(timezone.utc).isoformat(),
                backend="local_spool",
                error=f"postgres_failed: {exc}",
                receipt=receipt,
            )

    def record_receipt(self, receipt: RuntimeReceipt) -> ProvenanceResult:
        """Persist an already-signed receipt. Prefer record_receipt_builder."""
        return self.record_receipt_builder(lambda _previous: receipt)

    def load_receipts(self) -> list[RuntimeReceipt]:
        """Load receipts from the local spool in order."""
        from .receipt import validate_receipt_dict

        path = self._spool_path()
        if not path.exists():
            return []
        receipts: list[RuntimeReceipt] = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                record = json.loads(line)
                if "receipt" in record:
                    receipts.append(validate_receipt_dict(record["receipt"]))
                else:
                    receipts.append(validate_receipt_dict(record))
        return receipts

    def has_attestation(self, attestation_id: str) -> bool:
        """Return True if an attestation with this id is already stored."""
        if self._engine:
            try:
                from sqlalchemy import text

                row = self._engine.execute(
                    text(
                        "SELECT 1 FROM provenance.moscript_receipts "
                        "WHERE attestation_id = :id"
                    ),
                    {"id": attestation_id},
                ).mappings().first()
                if row is not None:
                    return True
            except Exception:
                pass
        path = self._spool_path()
        if not path.exists():
            return False
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                record = json.loads(line)
                if record.get("attestation_id") == attestation_id:
                    return True
        return False

    def get_receipt(self, attestation_id: str) -> RuntimeReceipt | None:
        """Return the stored receipt for an attestation id, if any."""
        if self._engine:
            try:
                from sqlalchemy import text

                row = self._engine.execute(
                    text(
                        "SELECT receipt FROM provenance.moscript_receipts "
                        "WHERE attestation_id = :id"
                    ),
                    {"id": attestation_id},
                ).mappings().first()
                if row is not None:
                    return validate_receipt_dict(json.loads(row["receipt"]))
            except Exception:
                pass
        path = self._spool_path()
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                record = json.loads(line)
                if record.get("attestation_id") == attestation_id:
                    return validate_receipt_dict(record["receipt"])
        return None


def verify_chain(
    receipts: list[RuntimeReceipt],
    public_keys: dict[str, Any],
) -> ChainResult:
    """Verify every signature and every previous-receipt hash link."""
    if not receipts:
        return ChainResult(valid=True, checked=0)

    prev_hash: str | None = None
    for i, receipt in enumerate(receipts):
        pub = public_keys.get(receipt.key_id)
        if pub is None:
            return ChainResult(
                valid=False,
                checked=i,
                first_invalid_index=i,
                first_invalid_reason=f"unknown_key_id: {receipt.key_id}",
            )
        try:
            verify_receipt(receipt, pub)
        except Exception as exc:
            return ChainResult(
                valid=False,
                checked=i,
                first_invalid_index=i,
                first_invalid_reason=f"signature_verification_failed: {exc}",
            )
        if i > 0:
            if receipt.previous_receipt_hash != prev_hash:
                return ChainResult(
                    valid=False,
                    checked=i,
                    first_invalid_index=i,
                    first_invalid_reason="chain_continuity_broken",
                )
        prev_hash = receipt.receipt_hash
    return ChainResult(valid=True, checked=len(receipts))
