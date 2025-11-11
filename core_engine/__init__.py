"""Bridge package so backend can import the root `core_engine` modules."""
from pathlib import Path

_repo_root = Path(__file__).resolve().parents[2]
_actual_core_engine = _repo_root / "core_engine"

if not _actual_core_engine.exists():
    raise ImportError(f"Expected core_engine package at {_actual_core_engine}")

__path__ = [str(_actual_core_engine)]
