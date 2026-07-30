import pytest
from fastapi.testclient import TestClient
from api.main import app
from core.fgrid.graph import fgrid_graph

client = TestClient(app)

def test_full_stack_integration():
    # Ensure graph is clear initially
    fgrid_graph.clear()

    # 1. Access root and verify online status
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json()["status"] == "Online"

    # 2. Create a project entity through the API
    project_payload = {
        "id": "project.integration_proj",
        "type": "Project",
        "title": "Integration Project",
        "owner": "Mo",
        "state": "Active",
        "tags": ["integration", "test"],
        "metadata": {"description": "Full-stack integration test project"}
    }
    resp = client.post("/api/fgrid/entities", json=project_payload)
    assert resp.status_code == 201
    assert resp.json()["id"] == "project.integration_proj"

    # 3. Create a task entity through the API
    task_payload = {
        "id": "task.integration_task",
        "type": "Task",
        "title": "Integration Task",
        "owner": "Mo",
        "state": "Active",
        "tags": ["integration", "test"],
        "metadata": {"status": "Pending"}
    }
    resp = client.post("/api/fgrid/entities", json=task_payload)
    assert resp.status_code == 201
    assert resp.json()["id"] == "task.integration_task"

    # 4. Create a relationship linking Project -> Task through the API
    rel_payload = {
        "source_id": "project.integration_proj",
        "target_id": "task.integration_task",
        "relation_type": "contains_task",
        "weight": 1.0,
        "metadata": {}
    }
    resp = client.post("/api/fgrid/relationships", json=rel_payload)
    assert resp.status_code == 201
    assert resp.json()["relation_type"] == "contains_task"

    # 5. Execute one cortex tick through the API
    resp = client.post("/api/runtime/tick")
    assert resp.status_code == 200
    actions = resp.json()["actions_taken"]
    assert len(actions) > 0
    assert any("Formulated plan" in action for action in actions)

    # 6. Retrieve the updated state of the task through the API and verify status changed
    resp = client.get("/api/fgrid/entities/task.integration_task")
    assert resp.status_code == 200
    task_data = resp.json()
    assert task_data["metadata"]["status"] == "Planning"

    # Also verify that a Plan was created in the graph for the task
    resp = client.get("/api/fgrid/entities")
    assert resp.status_code == 200
    entities = resp.json()
    entity_ids = [e["id"] for e in entities]
    assert "plan.integration_task" in entity_ids
