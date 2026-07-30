import pytest
from core.fgrid.models import MoStarEntity, Entity
from core.fgrid.graph import fgrid_graph

@pytest.mark.asyncio
async def test_runtime_bootstrap(bootstrapped_runtime):
    # Verify core companion exists
    mostar = fgrid_graph.get_entity("mostar.ai")
    assert mostar is not None
    assert isinstance(mostar, MoStarEntity)
    
    # Verify personas are loaded and registered
    persona_prime = fgrid_graph.get_entity("persona.prime")
    assert persona_prime is not None
    assert persona_prime.type == "Persona"

    # Verify user Mo is registered
    mo = fgrid_graph.get_entity("person.mo")
    assert mo is not None
    assert mo.type == "Person"

@pytest.mark.asyncio
async def test_execute_user_command(bootstrapped_runtime):
    res = await bootstrapped_runtime.execute_user_command("Upgrade planner subsystem", "prime")
    assert "response" in res
    assert res["persona"] == "Prime"
    
    # Verify interaction recorded in FGrid
    interaction = fgrid_graph.get_entity(res["interaction_id"])
    assert interaction is not None
    assert interaction.metadata["prompt"] == "Upgrade planner subsystem"

@pytest.mark.asyncio
async def test_executive_cortex_tick(bootstrapped_runtime):
    # 1. Manually add an active task to the graph
    task = Entity(
        id="task.test_upgrade",
        type="Task",
        title="Test Planner Upgrade",
        owner="Mo",
        metadata={"status": "Pending"}
    )
    fgrid_graph.add_entity(task)
    
    # 2. Execute tick 1: should formulate plan
    actions = await bootstrapped_runtime.tick()
    assert len(actions) == 1
    assert "Formulated plan" in actions[0]
    
    # Task state should update to Planning
    updated_task = fgrid_graph.get_entity("task.test_upgrade")
    assert updated_task.metadata["status"] == "Planning"
    
    # 3. Execute ticks to advance plan
    actions = await bootstrapped_runtime.tick()
    assert "Executing step" in actions[0]
    
    actions = await bootstrapped_runtime.tick()
    assert "Executing step" in actions[0]
    
    actions = await bootstrapped_runtime.tick()
    assert "Executing step" in actions[0]
    
    # 4. Final tick should complete the task
    actions = await bootstrapped_runtime.tick()
    assert "Completed task" in actions[0]
    
    final_task = fgrid_graph.get_entity("task.test_upgrade")
    assert final_task.metadata["status"] == "Completed"
