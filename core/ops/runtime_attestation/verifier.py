"""Independent runtime attestation verifier."""

from __future__ import annotations

import hashlib
import hmac
from typing import Any

from core.ops.runtime_attestation.manifest import (
    build_runtime_manifest,
    git_tree_clean,
    recompute_and_compare,
    runtime_digest_from_manifest,
)
from core.ops.runtime_attestation.models import GridReadiness, RuntimeIdentity
from core.ops.runtime_attestation.store import PostgresAttestationStore


def canonical_json(value: Any) -> str:
    import json
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


class RuntimeVerifier:
    def __init__(self, store: PostgresAttestationStore):
        self.store = store

    def verify(self) -> GridReadiness:
        failures = []

        try:
            manifest = build_runtime_manifest()
        except Exception as exc:
            failures.append(f"manifest build failed: {exc}")
            return GridReadiness(
                ready=False,
                runtime_verified=False,
                seal_verified=False,
                attestation_id=None,
                failures=failures,
            )

        if not git_tree_clean():
            failures.append("WORKTREE_UNCOMMITTED")

        component_failures = recompute_and_compare(manifest)
        failures.extend(component_failures)

        attestation = self.store.get_active(manifest["runtime_digest"])
        if attestation is None:
            failures.append("NO_ATTESTATION_RECORD")
        elif attestation["verification_status"] != "verified":
            failures.append(
                f"ATTESTATION_{attestation['verification_status'].upper()}"
            )

        seal_verified = False
        if attestation is not None and not component_failures:
            latest = self.store.latest_seal(str(attestation["attestation_id"]))
            if latest is None:
                failures.append("NO_DEEP_SEAL")
            else:
                # Verify seal chain by recompute
                expected = hashlib.sha256(
                    canonical_json({
                        "previous_hash": latest["previous_hash"],
                        "runtime_digest": latest["runtime_digest"],
                        "attestation_id": latest["attestation_id"],
                        "created_at": latest["created_at"],
                    }).encode("utf-8")
                ).hexdigest()

                if hmac.compare_digest(expected, latest["seal_hash"]):
                    seal_verified = True
                else:
                    failures.append("SEAL_HASH_MISMATCH")

        runtime_verified = (
            attestation is not None
            and attestation["verification_status"] == "verified"
            and not component_failures
        )

        ready = (
            runtime_verified
            and seal_verified
            and git_tree_clean()
            and not failures
        )

        return GridReadiness(
            ready=ready,
            runtime_verified=runtime_verified,
            seal_verified=seal_verified,
            attestation_id=(
                str(attestation["attestation_id"]) if attestation else None
            ),
            failures=failures,
        )

    def identity(self) -> dict[str, Any]:
        manifest = build_runtime_manifest()
        attestation = self.store.get_active(manifest["runtime_digest"])

        result = {
            "status": "aligned",
            "operation": "mo-grid-identity-002",
            "identity": {
                "system_id": manifest["system_id"],
                "runtime_id": manifest["runtime_id"],
                "runtime_version": manifest["runtime_version"],
                "build_commit": manifest["build_commit"],
                "runtime_digest": manifest["runtime_digest"],
            },
            "attestation": {
                "status": (
                    "verified"
                    if attestation is not None
                    and attestation["verification_status"] == "verified"
                    else "unverified"
                ),
                "attestation_id": (
                    str(attestation["attestation_id"])
                    if attestation
                    else None
                ),
                "verified_at": (
                    attestation["verified_at"] if attestation else None
                ),
            },
        }

        return result
