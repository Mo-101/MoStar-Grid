from datetime import datetime
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

class Entity(BaseModel):
    id: str
    type: str = Field(description="The type of the entity, e.g., 'Person', 'Project', 'AI Companion'")
    title: str
    owner: str = "System"
    created: datetime = Field(default_factory=datetime.utcnow)
    updated: datetime = Field(default_factory=datetime.utcnow)
    state: str = "Active"
    confidence: float = 1.0
    importance: int = 5
    tags: List[str] = []
    metadata: Dict[str, Any] = {}

class Relationship(BaseModel):
    source_id: str
    target_id: str
    relation_type: str  # e.g., 'manages', 'observes', 'protects', 'depends_on'
    weight: float = 1.0
    metadata: Dict[str, Any] = {}

class CognitionState(BaseModel):
    current_focus: Optional[str] = None
    active_personas: List[str] = []
    runtime_health: str = "Healthy"

class MoStarEntity(Entity):
    type: str = "AI Companion"
    class_type: str = Field(default="Executive Intelligence", serialization_alias="class", validation_alias="class")
    version: str = "Prime"
    
    # Internal Graph Clusters represented as structured state
    cognition: CognitionState = Field(default_factory=CognitionState)
    active_tasks: List[str] = []      # List of Task Entity IDs
    active_projects: List[str] = []   # List of Project Entity IDs
    memory_layers: List[str] = []     # e.g., ['working', 'vault']
    capabilities: List[str] = []      # List of Skill/Tool Entity IDs
    connected_tools: List[str] = []   # List of Tool Entity IDs
