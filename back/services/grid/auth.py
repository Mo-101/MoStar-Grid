# back/services/grid/auth.py
"""
MoStar Grid — Authentication & Authorization Layer
Minimal token-based auth for the TruthGate and admin endpoints.
"""
import os
from fastapi import Request, HTTPException, status

# Session token must be provided by the environment unless local auth is disabled.
MOSTAR_SESSION_TOKEN = os.getenv("MOSTAR_SESSION_TOKEN")

ROLE_PERMISSIONS = {
    "admin": {"read", "write", "execute", "audit"},
    "operator": {"read", "execute", "audit"},
    "viewer": {"read"},
}


def get_current_user_and_role(request: Request) -> dict:
    """
    Extract and validate the session token from X-MoStar-Token header.
    Returns a user dict with role information.
    """
    token = request.headers.get("X-MoStar-Token")

    # Allow unauthenticated access in development when auth is disabled
    if os.getenv("GRID_AUTH_DISABLED", "false").lower() == "true":
        return {"user": "dev-local", "role": "admin", "authenticated": False}

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-MoStar-Token header",
        )

    if not MOSTAR_SESSION_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MoStar session token is not configured",
        )

    if token != MOSTAR_SESSION_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid session token",
        )

    return {"user": "mostar-operator", "role": "admin", "authenticated": True}


def verify_permission(action: str, user: dict) -> None:
    """
    Verify that the user's role grants the requested action.
    Raises HTTP 403 if permission is denied.
    """
    role = user.get("role", "viewer")
    allowed = ROLE_PERMISSIONS.get(role, set())
    if action not in allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role '{role}' does not have '{action}' permission",
        )
