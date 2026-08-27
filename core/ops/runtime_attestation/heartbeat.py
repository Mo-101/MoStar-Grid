"""MoScript logic for mo-grid-heartbeat-001."""

from __future__ import annotations

from typing import Any

from core.ops.runtime_attestation.models import GridReadiness


def _runtime_check(
    runtime_health,
    name: str,
    expect_ready: bool = True,
) -> str | None:
    dep = runtime_health.dependencies.get(name)
    if dep is None:
        return f"{name.upper()}_UNKNOWN"
    if expect_ready and dep.status != "ready":
        return f"{name.upper()}_{dep.status.upper()}"
    return None


def execute_grid_heartbeat(context: dict[str, Any]) -> GridReadiness:
    """Derive GRID_MIND_READY from identity + runtime health.

    This is the only component allowed to derive GRID_MIND_READY=True.
    """
    verifier = context.get("verifier")
    runtime_health = context.get("runtime_health")

    if verifier is None:
        return GridReadiness(
            ready=False,
            runtime_verified=False,
            seal_verified=False,
            attestation_id=None,
            failures=["NO_VERIFIER_IN_CONTEXT"],
        )

    identity = verifier.verify()
    failures = list(identity.failures)

    if runtime_health is not None:
        for name in ("local_postgres", "neo4j", "ollama"):
            failure = _runtime_check(runtime_health, name)
            if failure:
                failures.append(failure)
    else:
        failures.append("NO_RUNTIME_HEALTH_IN_CONTEXT")

    # The deep-seal identity must also have a verified runtime and seal.
    runtime_verified = identity.runtime_verified and identity.seal_verified

    ready = identity.ready and runtime_verified and not failures

    return GridReadiness(
        ready=ready,
        runtime_verified=identity.runtime_verified,
        seal_verified=identity.seal_verified,
        attestation_id=identity.attestation_id,
        failures=failures,
    )
