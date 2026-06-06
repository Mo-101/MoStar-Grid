"""Grid service package exports."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .orchestrator import (
        CommitFailedError,
        CommitForbiddenError,
        CommitResult,
        GridOrchestrator,
        GridResponse,
    )

__all__ = [
    "CommitFailedError",
    "CommitForbiddenError",
    "CommitResult",
    "GridOrchestrator",
    "GridResponse",
]


def __getattr__(name: str):
    if name in __all__:
        from . import orchestrator

        return getattr(orchestrator, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
