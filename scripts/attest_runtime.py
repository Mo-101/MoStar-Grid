"""Generate a runtime attestation manifest and record it in PostgreSQL."""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from control_plane_runtime import validate_sovereign_database_url
from core.ops.runtime_attestation import (
    PostgresAttestationStore,
    build_runtime_manifest,
    canonical_json,
)


def main() -> None:
    database_url = os.environ["DATABASE_URL"]
    validate_sovereign_database_url(database_url)

    manifest = build_runtime_manifest()
    print("Runtime manifest:")
    print(json.dumps(manifest, indent=2, sort_keys=True))

    store = PostgresAttestationStore(database_url)

    attestation_id = store.record_attestation(
        manifest, verification_status="verified"
    )
    print(f"Attestation recorded: {attestation_id}")

    previous = store.latest_seal(attestation_id)
    previous_hash = previous["seal_hash"] if previous else None

    created_at = datetime.now(timezone.utc)
    base = {
        "previous_hash": previous_hash,
        "runtime_digest": manifest["runtime_digest"],
        "attestation_id": attestation_id,
        "created_at": created_at.isoformat(),
    }

    seal_hash = hashlib.sha256(canonical_json(base).encode("utf-8")).hexdigest()
    sequence = store.record_seal(
        attestation_id=attestation_id,
        runtime_digest=manifest["runtime_digest"],
        previous_hash=previous_hash,
        seal_hash=seal_hash,
        created_at=created_at,
    )
    print(f"Deep seal recorded: sequence={sequence} hash={seal_hash}")


if __name__ == "__main__":
    main()
