from core.soul.identity import get_mostar_identity
from core.soul.mission import get_mission_entity
from core.soul.values import get_values_entities

def test_mostar_identity_structure():
    mostar = get_mostar_identity()
    assert mostar.id == "mostar.ai"
    assert mostar.type == "AI Companion"
    assert mostar.cognition.runtime_health == "Healthy"
    assert "working" in mostar.memory_layers

def test_soul_mission_entity():
    mission = get_mission_entity()
    assert mission.id == "soul.mission"
    assert mission.type == "Mission"
    assert "FlameBorn" in mission.metadata["description"]

def test_core_values_covenant():
    values = get_values_entities()
    assert len(values) >= 3
    ids = [v.id for v in values]
    assert "soul.values.sovereignty" in ids
    assert "soul.values.truth" in ids
