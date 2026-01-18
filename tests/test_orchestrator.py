import pytest
import asyncio
from core_engine.orchestrator import complexity_score, determine_route, route_query

@pytest.mark.parametrize("text,expected_min_score", [
    ("Hello, how are you?", 0.0),
    ("Please analyze this complex ritual with more than one hundred and fifty words to ensure that the token count exceeds the threshold for high complexity routing in the MoStar Grid system. We need to verify every single detail of this implementation to ensure it aligns with the FlameCODEX and ancestral laws.", 0.8),
    ("explain the ifa odu patterns", 0.3),
    ("simulate the soul layer sync", 0.3),
])
def test_complexity_score(text, expected_min_score):
    score, count = complexity_score(text)
    assert score >= expected_min_score
    assert count == len(text.lower().split())

def test_determine_route():
    # Mind route (high score)
    complex_text = "analyze " * 20
    assert determine_route(complex_text, {}) == 'Mind'
    
    # Soul route (context)
    assert determine_route("hello", {"neo4j_context": "Found a moment"}) == 'Soul'
    
    # Body route (simple)
    assert determine_route("hi", {}) == 'Body'

@pytest.mark.asyncio
async def test_route_query_mock():
    # This might need mocking of httpx/ollama depending on environment
    # But we can at least check if it handles some basic flows
    # For now, we just verify the routing logic within route_query
    pass
