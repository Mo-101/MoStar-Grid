"""Shared fixtures for MoMind contract tests."""
from __future__ import annotations

import pathlib

import pytest

from moscript.runtime.contract_engine import GovernanceEngine

CONTRACTS_DIR = pathlib.Path("core/protocols/moscript/contracts")


@pytest.fixture(scope="session")
def engine() -> GovernanceEngine:
    return GovernanceEngine.from_path(CONTRACTS_DIR)
