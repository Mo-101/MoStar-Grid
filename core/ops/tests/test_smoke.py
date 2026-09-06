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


def test_validate_consistency_empty_context_fails():
    engine = TruthEngine()
    report = asyncio.run(engine.validate_consistency("content", ["Agent"], []))
    assert not report.passed
    assert any("existing_context empty" in f for f in report.failures)


def test_validate_consistency_duplicate_fails():
    engine = TruthEngine()
    context = [{"content": "content", "id": "n1", "_labels": ["Agent"]}]
    report = asyncio.run(engine.validate_consistency("content", ["Agent"], context))
    assert not report.passed
    assert any("Ikang" in f for f in report.failures)


def test_validate_consistency_disconnected_labels_fails():
    engine = TruthEngine()
    context = [{"content": "some content", "id": "n1", "_labels": ["Agent"]}]
    report = asyncio.run(
        engine.validate_consistency("new content about agent Mo", ["NonExistent"], context)
    )
    assert not report.passed
    assert any("Mmọng" in f for f in report.failures)


def test_validate_consistency_empty_content_fails():
    engine = TruthEngine()
    context = [{"content": "some content", "id": "n1", "_labels": ["Agent"]}]
    report = asyncio.run(engine.validate_consistency("", ["Agent"], context))
    assert not report.passed
    assert any("Afim" in f for f in report.failures)


def test_validate_consistency_ungrounded_content_fails():
    engine = TruthEngine()
    context = [{"name": "Mo", "id": "n1", "_labels": ["Agent"]}]
    report = asyncio.run(
        engine.validate_consistency("completely new concept not found", ["Agent"], context)
    )
    assert not report.passed
    assert any("Isong" in f for f in report.failures)


def test_validate_consistency_pass_and_seal():
    engine = TruthEngine()
    context = [{"name": "Mo", "content": "Mo is an agent", "id": "n1", "_labels": ["Agent"]}]
    report = asyncio.run(engine.validate_consistency("proposal about Mo", ["Agent"], context))
    assert report.passed
    assert report.seal is not None
    assert len(report.seal) == 32
    assert report.scores["ikang"] == 1.0
    assert report.scores["mmong"] == 1.0
    assert report.scores["afim"] == 1.0
    assert report.scores["isong"] == 1.0


def test_validate_consistency_seal_canonicalization():
    engine = TruthEngine()
    context = [{"name": "Mo", "id": "n1", "_labels": ["Agent"]}]
    report1 = asyncio.run(engine.validate_consistency("proposal about Mo", ["Agent"], context))
    report2 = asyncio.run(engine.validate_consistency("proposal about Mo", ["Agent"], context))
    assert report1.passed and report2.passed
    assert report1.seal == report2.seal
    report3 = asyncio.run(engine.validate_consistency("different proposal", ["Agent"], context))
    assert report3.seal != report1.seal
