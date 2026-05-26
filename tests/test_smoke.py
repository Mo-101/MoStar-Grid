"""
Grid Smoke Test — Verify all subsystems boot.
Run: PYTHONPATH=. python -m pytest tests/test_smoke.py -v
"""
import asyncio
import pytest
from grid.config import SEAL_GLYPH
from truth_engine import TruthEngine
from woo import WooGate
from moscript import MoScriptEngine
from soul import SoulPrint


def test_truth_engine_passes_good_response():
    engine = TruthEngine()
    verdict = engine.evaluate(
        response="The Grid is a sovereign intelligence system built on Neo4j and Ollama.",
        query="What is the Grid?",
        context_count=5,
    )
    assert verdict.passed, f"Expected pass, got failures: {verdict.failures}"
    assert verdict.seal == SEAL_GLYPH


def test_truth_engine_fails_empty():
    engine = TruthEngine()
    verdict = engine.evaluate(response="", query="test")
    assert not verdict.passed


def test_woo_auto_approves_standard():
    engine = TruthEngine()
    verdict = engine.evaluate(
        response="The test query result shows a clear and grounded response with verified data from the knowledge graph.",
        query="test query",
        context_count=5,
    )
    woo = WooGate()
    judgment = woo.judge(verdict, action_type="response")
    assert judgment.approved


def test_moscript_startup():
    engine = MoScriptEngine()
    results = engine.fire_trigger("on_startup", {
        "neo4j_connected": True,
        "ollama_connected": True,
    })
    assert len(results) >= 2
    assert all(r["fired"] for r in results)


def test_soul_identity():
    soul = SoulPrint()
    declaration = soul.declare()
    assert "MoStar Grid" in declaration
    assert "Flame Architect" in declaration
    assert SEAL_GLYPH in declaration


def test_soul_elements():
    soul = SoulPrint()
    data = soul.to_dict()
    assert "ikang" in data["elements"]
    assert data["elements"]["ikang"]["glyph"] == "🜂"
    assert "eka_isong" in data["sacred"]
