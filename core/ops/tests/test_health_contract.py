import os

from fastapi.testclient import TestClient

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql://grid_runtime:test@127.0.0.1:5432/grid",
)

from grid.api import app, orchestrator
from grid.runtime_health import RuntimeHealth


class DatabaseMustNotBeTouched:
    def __getattr__(self, name):
        raise AssertionError(f"liveness touched database through {name}")


def test_liveness_does_not_touch_database():
    original_provider = orchestrator.control_plane.provider
    original_health = orchestrator.runtime_health
    try:
        orchestrator.control_plane.provider = DatabaseMustNotBeTouched()
        orchestrator.runtime_health = RuntimeHealth()
        orchestrator.runtime_health.mark_process_initialized()

        response = TestClient(app).get("/health/live")

        assert response.status_code == 200
        assert response.json()["status"] == "alive"
        assert response.json()["process_initialized"] is True
    finally:
        orchestrator.control_plane.provider = original_provider
        orchestrator.runtime_health = original_health


def test_local_postgres_failure_blocks_mutation():
    original_health = orchestrator.runtime_health
    try:
        orchestrator.runtime_health = RuntimeHealth()
        orchestrator.runtime_health.mark_process_initialized()
        orchestrator.runtime_health.mark_governance_blocked(
            "POSTGRES_UNREACHABLE"
        )

        response = TestClient(app).post(
            "/api/propose",
            json={"canon_input": "must not bypass governance"},
        )

        assert response.status_code == 503
        assert response.json()["detail"] == {
            "code": "GOVERNANCE_NOT_READY",
            "dependency": "local_postgres",
            "retryable": True,
        }
    finally:
        orchestrator.runtime_health = original_health
