import pytest

from control_plane_runtime import validate_sovereign_database_url
from grid.runtime_health import GridMode, RuntimeHealth, postgres_error_code


def test_local_postgres_failure_blocks_readiness_but_keeps_process_live():
    health = RuntimeHealth()
    health.mark_process_initialized()
    health.mark_up("neo4j")
    health.mark_governance_blocked("POSTGRES_UNREACHABLE")

    snapshot = health.snapshot()
    assert snapshot["live"] is True
    assert snapshot["ready"] is False
    assert snapshot["mode"] == GridMode.LOCAL_POSTGRES_BLOCKED.value


def test_ollama_failure_does_not_block_readiness():
    health = RuntimeHealth()
    health.mark_process_initialized()
    health.mark_up("neo4j")
    health.mark_governance_ready()
    health.mark_down("ollama", "OLLAMA_UNAVAILABLE")

    assert health.ready is True
    assert health.mode == GridMode.READY


def test_postgres_authentication_error_is_classified():
    assert postgres_error_code(
        "password authentication failed for user grid_runtime"
    ) == "POSTGRES_AUTH_FAILED"


def test_neon_url_is_rejected():
    with pytest.raises(RuntimeError):
        validate_sovereign_database_url(
            "postgresql://user:pass@example.neon.tech/grid"
        )


def test_local_postgres_is_accepted():
    validate_sovereign_database_url(
        "postgresql://grid_runtime:pass@127.0.0.1:5432/grid"
    )


def test_readiness_requires_local_postgres_and_neo4j():
    health = RuntimeHealth()
    health.mark_process_initialized()
    health.mark_governance_ready()
    assert health.ready is False

    health.mark_up("neo4j")
    assert health.ready is True
