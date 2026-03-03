"""Bridge package so backend can import the root `core_engine` modules."""
from pathlib import Path

_this_dir = Path(__file__).resolve().parent
_repo_root = _this_dir.parent
_actual_core_engine = _repo_root / "backend" / "core_engine"

if not _actual_core_engine.exists():
    # Fallback: try repo root core_engine
    _actual_core_engine = _repo_root / "core_engine"

if not _actual_core_engine.exists():
    raise ImportError(f"Expected core_engine package at {_actual_core_engine}")

__path__ = [str(_actual_core_engine)]

# Export MoStar Moments system
try:
    from core_engine.mostar_moments import (
        MoStarMoment,
        MoStarMomentsManager,
        Era,
        TriggerType,
        mo_star_moment,
        get_canonical_moments
    )
except ImportError:
    pass  # Module not yet available
