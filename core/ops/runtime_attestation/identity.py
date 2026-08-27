"""MoScript logic for mo-grid-identity-002."""

from __future__ import annotations

from typing import Any


def execute_grid_identity(context: dict[str, Any]) -> dict[str, Any]:
    """Report the verified runtime identity; never attest itself."""
    verifier = context.get("verifier")
    if verifier is None:
        return {
            "status": "denied",
            "operation": "mo-grid-identity-002",
            "reason": "NO_VERIFIER_IN_CONTEXT",
        }
    return verifier.identity()
