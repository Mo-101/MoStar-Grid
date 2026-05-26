from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class GridExecutionResult:
    executed: bool
    reason: str
    actions: list[str] = field(default_factory=list)


class GridOrchestrator:
    """Compatibility executor for the advisory governance flow."""

    def execute(self, verdict) -> GridExecutionResult:
        return GridExecutionResult(
            executed=bool(verdict.allowed),
            reason=verdict.reason,
            actions=list(verdict.actions),
        )
