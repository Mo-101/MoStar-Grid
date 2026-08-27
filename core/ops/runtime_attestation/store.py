"""PostgreSQL persistence for runtime attestation and deep seals."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

import psycopg

from core.ops.runtime_attestation.manifest import canonical_json


class PostgresAttestationStore:
    def __init__(self, database_url: str):
        self.database_url = database_url

    def _connect(self):
        return psycopg.connect(self.database_url, connect_timeout=10)

    def get_active(self, runtime_digest: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT attestation_id, runtime_id, runtime_version,
                           build_commit, manifest, verification_status,
                           verified_at
                    FROM grid.runtime_attestation
                    WHERE runtime_digest = %s
                    ORDER BY created_at DESC
                    LIMIT 1
                    """,
                    (runtime_digest,),
                )
                row = cur.fetchone()
        if row is None:
            return None
        return {
            "attestation_id": str(row[0]),
            "runtime_id": row[1],
            "runtime_version": row[2],
            "build_commit": row[3],
            "manifest": row[4],
            "verification_status": row[5],
            "verified_at": (
                row[6].astimezone(timezone.utc).isoformat()
                if row[6]
                else None
            ),
        }

    def latest_seal(self, attestation_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT sequence, attestation_id, runtime_digest,
                           previous_hash, seal_hash, created_at
                    FROM grid.runtime_seals
                    WHERE attestation_id = %s
                    ORDER BY sequence DESC
                    LIMIT 1
                    """,
                    (attestation_id,),
                )
                row = cur.fetchone()
        if row is None:
            return None
        return {
            "sequence": row[0],
            "attestation_id": str(row[1]),
            "runtime_digest": row[2],
            "previous_hash": row[3],
            "seal_hash": row[4],
            "created_at": (
                row[5].astimezone(timezone.utc).isoformat()
                if row[5]
                else None
            ),
        }

    def record_attestation(
        self,
        manifest: dict[str, Any],
        verification_status: str = "verified",
    ) -> str:
        attestation_id = str(uuid.uuid4())
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO grid.runtime_attestation (
                        attestation_id,
                        runtime_id,
                        runtime_version,
                        build_commit,
                        runtime_digest,
                        manifest,
                        verification_status,
                        verified_at,
                        created_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (runtime_digest)
                    DO UPDATE SET
                        verification_status = EXCLUDED.verification_status,
                        verified_at = EXCLUDED.verified_at
                    RETURNING attestation_id
                    """,
                    (
                        attestation_id,
                        manifest["runtime_id"],
                        manifest["runtime_version"],
                        manifest["build_commit"],
                        manifest["runtime_digest"],
                        canonical_json(manifest),
                        verification_status,
                        datetime.now(timezone.utc),
                        datetime.now(timezone.utc),
                    ),
                )
                row = cur.fetchone()
                attestation_id = str(row[0])
            conn.commit()
        return attestation_id

    def record_seal(
        self,
        attestation_id: str,
        runtime_digest: str,
        previous_hash: str | None,
        seal_hash: str,
        created_at: datetime,
    ) -> int:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO grid.runtime_seals (
                        attestation_id,
                        runtime_digest,
                        previous_hash,
                        seal_hash,
                        created_at
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING sequence
                    """,
                    (
                        attestation_id,
                        runtime_digest,
                        previous_hash,
                        seal_hash,
                        created_at,
                    ),
                )
                row = cur.fetchone()
                sequence = row[0]
            conn.commit()
        return sequence
