"""Regression tests for the Phase 0 retrieve_context() retrieval incident.

Bug: the Cypher used the named placeholder $query, but the driver call
supplied a parameter named query_param, so the primary full-text path (and
the old unbounded MATCH fallback) always raised, the exception was silently
swallowed, and callers received an empty list indistinguishable from a
genuine zero-match result.

These tests pin the fix:
  1. the driver receives a parameter literally named `query`
  2. a successful query with matches returns the matched nodes
  3. a successful query with zero matches returns [] (not an error)
  4. an infrastructure/driver failure raises GovernedRetrievalUnavailable
     instead of being swallowed or silently returning []
  5. no driver connection raises GovernedRetrievalUnavailable
  6. there is no unbounded MATCH fallback query executed on failure
"""
import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from mindgraph import GovernedRetrievalUnavailable, MindGraph


def _mindgraph_with_session(session_mock):
    """Build a MindGraph whose driver.session(...) context manager yields session_mock."""
    mg = MindGraph()
    driver = MagicMock()
    session_ctx = MagicMock()
    session_ctx.__aenter__ = AsyncMock(return_value=session_mock)
    session_ctx.__aexit__ = AsyncMock(return_value=False)
    driver.session.return_value = session_ctx
    mg._driver = driver
    return mg


def test_retrieve_context_uses_correct_named_parameter():
    """The Cypher references $query; the driver call must bind `query=`."""
    session = MagicMock()
    result = MagicMock()
    result.data = AsyncMock(return_value=[])
    session.run = AsyncMock(return_value=result)
    mg = _mindgraph_with_session(session)

    asyncio.run(mg.retrieve_context("outbreak response", limit=5))

    assert session.run.call_count == 1
    _, kwargs = session.run.call_args
    assert kwargs.get("query") == "outbreak response"
    assert "query_param" not in kwargs


def test_retrieve_context_returns_matches_on_success():
    session = MagicMock()
    result = MagicMock()
    result.data = AsyncMock(return_value=[{"node": {"id": "n1", "_score": 0.9}}])
    session.run = AsyncMock(return_value=result)
    mg = _mindgraph_with_session(session)

    records = asyncio.run(mg.retrieve_context("known term"))

    assert records == [{"id": "n1", "_score": 0.9}]


def test_retrieve_context_zero_matches_is_a_successful_empty_result():
    session = MagicMock()
    result = MagicMock()
    result.data = AsyncMock(return_value=[])
    session.run = AsyncMock(return_value=result)
    mg = _mindgraph_with_session(session)

    records = asyncio.run(mg.retrieve_context("no such term"))

    assert records == []


def test_retrieve_context_infrastructure_failure_is_not_swallowed():
    """A driver-level failure must raise, never be reported as [] ."""
    session = MagicMock()
    session.run = AsyncMock(side_effect=RuntimeError("index gridSearch does not exist"))
    mg = _mindgraph_with_session(session)

    with pytest.raises(GovernedRetrievalUnavailable):
        asyncio.run(mg.retrieve_context("anything"))

    # Exactly one attempt — no silent unbounded MATCH fallback query.
    assert session.run.call_count == 1


def test_retrieve_context_without_driver_fails_closed():
    mg = MindGraph()
    assert mg._driver is None

    with pytest.raises(GovernedRetrievalUnavailable):
        asyncio.run(mg.retrieve_context("anything"))
