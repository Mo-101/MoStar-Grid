import pytest
from core.fgrid.graph import fgrid_graph
from core.runtime.runtime import MoStarRuntime

@pytest.fixture(autouse=True)
def clean_graph():
    """Ensures a clean graph before and after every test run."""
    fgrid_graph.clear()
    yield
    fgrid_graph.clear()

@pytest.fixture
def bootstrapped_runtime():
    """Provides a runtime instance that has already bootstrapped the core identity."""
    rt = MoStarRuntime()
    rt.bootstrap()
    return rt
