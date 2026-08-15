"""Explicit Grid lifecycle and dependency health."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class GridMode(str, Enum):
    BOOTING = "BOOTING"
    PROCESS_INITIALIZED = "PROCESS_INITIALIZED"
    LOCAL_POSTGRES_CONNECTING = "LOCAL_POSTGRES_CONNECTING"
    LOCAL_POSTGRES_READY = "LOCAL_POSTGRES_READY"
    LOCAL_POSTGRES_BLOCKED = "LOCAL_POSTGRES_BLOCKED"
    NEO4J_CONNECTING = "NEO4J_CONNECTING"
    NEO4J_READY = "NEO4J_READY"
    READY = "READY"
    DEGRADED = "DEGRADED"
    MAINTENANCE = "MAINTENANCE"


@dataclass
class DependencyState:
    status: str = "down"
    last_success_at: Optional[str] = None
    last_failure_at: Optional[str] = None
    error_code: Optional[str] = None


@dataclass
class RuntimeHealth:
    mode: GridMode = GridMode.BOOTING
    process_initialized: bool = False
    dependencies: dict[str, DependencyState] = field(default_factory=lambda: {
        "local_postgres": DependencyState(),
        "neo4j": DependencyState(),
        "ollama": DependencyState(),
    })

    @property
    def ready(self) -> bool:
        return (
            self.process_initialized
            and self.mode == GridMode.READY
            and self.dependencies["local_postgres"].status == "ready"
            and self.dependencies["neo4j"].status == "ready"
        )

    @property
    def governance_ready(self) -> bool:
        return self.dependencies["local_postgres"].status == "ready"

    def mark_process_initialized(self) -> None:
        self.process_initialized = True
        self.recompute_mode()

    def mark_connecting(self, dependency: str) -> None:
        self.dependencies[dependency].status = "connecting"
        self.recompute_mode()

    def mark_governance_ready(self) -> None:
        self.mark_up("local_postgres")

    def mark_governance_blocked(self, code: str) -> None:
        self.mark_down("local_postgres", code, blocked=True)

    def mark_up(self, dependency: str) -> None:
        state = self.dependencies[dependency]
        state.status = "ready"
        state.last_success_at = _now()
        state.error_code = None
        self.recompute_mode()

    def mark_down(self, dependency: str, error_code: str, *, blocked: bool = False) -> None:
        state = self.dependencies[dependency]
        state.status = "blocked" if blocked else "down"
        state.last_failure_at = _now()
        state.error_code = error_code
        self.recompute_mode()

    def recompute_mode(self) -> None:
        if not self.process_initialized:
            self.mode = GridMode.BOOTING
        elif self.dependencies["local_postgres"].status == "blocked":
            self.mode = GridMode.LOCAL_POSTGRES_BLOCKED
        elif (
            self.dependencies["local_postgres"].status == "ready"
            and self.dependencies["neo4j"].status == "ready"
        ):
            self.mode = GridMode.READY
        else:
            self.mode = GridMode.DEGRADED

    def snapshot(self) -> dict:
        return {
            "mode": self.mode.value,
            "live": self.process_initialized,
            "ready": self.ready,
            "dependencies": {
                name: asdict(state) for name, state in self.dependencies.items()
            },
        }


def postgres_error_code(error: BaseException | str) -> str:
    text = str(error).lower()
    if "schema missing" in text or "undefinedtable" in text:
        return "POSTGRES_SCHEMA_INVALID"
    if "pool" in text and ("exhaust" in text or "timeout" in text):
        return "POSTGRES_POOL_EXHAUSTED"
    if any(marker in text for marker in (
        "password authentication failed",
        "authentication failed",
        "invalid password",
        "sqlstate 28p01",
    )):
        return "POSTGRES_AUTH_FAILED"
    return "POSTGRES_UNREACHABLE"
