from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from core.fgrid.models import Entity, Relationship
from core.fgrid.graph import fgrid_graph
from core.runtime.runtime import MoStarRuntime

router = APIRouter()

# Simple Dependency injection to share the runtime instance
_runtime_instance: Optional[MoStarRuntime] = None

def get_runtime() -> MoStarRuntime:
    global _runtime_instance
    if _runtime_instance is None:
        _runtime_instance = MoStarRuntime()
        _runtime_instance.bootstrap()
    return _runtime_instance

class CommandRequest(BaseModel):
    prompt: str
    persona: str = "prime"

@router.post("/command", summary="Execute a command under a specified persona")
async def execute_command(req: CommandRequest, runtime: MoStarRuntime = Depends(get_runtime)):
    res = await runtime.execute_user_command(req.prompt, req.persona)
    if "error" in res:
        raise HTTPException(status_code=404, detail=res["error"])
    return res

@router.get("/fgrid/entities", response_model=List[Entity], summary="List all entities in FGrid")
def list_entities():
    return list(fgrid_graph.entities.values())

@router.get("/fgrid/entities/{entity_id}", response_model=Entity, summary="Retrieve a specific entity from FGrid")
def get_entity(entity_id: str):
    ent = fgrid_graph.get_entity(entity_id)
    if not ent:
        raise HTTPException(status_code=404, detail="Entity not found")
    return ent

@router.post("/fgrid/entities", response_model=Entity, status_code=201, summary="Register a new entity in FGrid")
def create_entity(entity: Entity):
    fgrid_graph.add_entity(entity)
    return entity

@router.get("/fgrid/relationships", response_model=List[Relationship], summary="List all relationships in FGrid")
def list_relationships():
    return fgrid_graph.relationships

@router.post("/fgrid/relationships", response_model=Relationship, status_code=201, summary="Register a new relationship in FGrid")
def create_relationship(relationship: Relationship):
    fgrid_graph.add_relationship(relationship)
    return relationship

@router.post("/runtime/tick", summary="Trigger a single manual Executive Cortex tick")
async def trigger_tick(runtime: MoStarRuntime = Depends(get_runtime)):
    actions = await runtime.tick()
    return {"status": "success", "actions_taken": actions}
