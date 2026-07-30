from typing import Dict, List, Tuple, Optional
from core.fgrid.models import Entity, Relationship

class FGridGraph:
    """An in-memory representation of the FGrid knowledge fabric for Sprint 1."""
    
    def __init__(self):
        self.entities: Dict[str, Entity] = {}
        self.relationships: List[Relationship] = []

    def add_entity(self, entity: Entity) -> None:
        self.entities[entity.id] = entity

    def get_entity(self, entity_id: str) -> Optional[Entity]:
        return self.entities.get(entity_id)

    def remove_entity(self, entity_id: str) -> None:
        if entity_id in self.entities:
            del self.entities[entity_id]
        # Remove any associated relationships
        self.relationships = [
            r for r in self.relationships 
            if r.source_id != entity_id and r.target_id != entity_id
        ]

    def add_relationship(self, relationship: Relationship) -> None:
        # Check if both entities exist in our graph first
        # For flexible graph construction, we don't strictly enforce but it's good practice
        self.relationships.append(relationship)

    def get_relationships(self, entity_id: str) -> List[Relationship]:
        """Get all relationships originating or terminating at entity_id."""
        return [
            r for r in self.relationships 
            if r.source_id == entity_id or r.target_id == entity_id
        ]

    def get_neighbors(self, entity_id: str, relation_type: Optional[str] = None) -> List[Tuple[Entity, str]]:
        """Get neighboring entities along with the relation direction/type."""
        neighbors = []
        for r in self.relationships:
            if relation_type and r.relation_type != relation_type:
                continue
            if r.source_id == entity_id:
                target = self.get_entity(r.target_id)
                if target:
                    neighbors.append((target, f"out:{r.relation_type}"))
            elif r.target_id == entity_id:
                source = self.get_entity(r.source_id)
                if source:
                    neighbors.append((source, f"in:{r.relation_type}"))
        return neighbors

    def find_entities_by_type(self, type_name: str) -> List[Entity]:
        return [e for e in self.entities.values() if e.type == type_name]

    def clear(self) -> None:
        self.entities.clear()
        self.relationships.clear()

# Global graph instance for Sprint 1
fgrid_graph = FGridGraph()
