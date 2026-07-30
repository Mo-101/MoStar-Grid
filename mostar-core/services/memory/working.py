from typing import List, Optional
from core.fgrid.models import Entity, Relationship
from core.fgrid.graph import fgrid_graph

class WorkingMemory:
    """Manages short-term cognitive focus and active conversation context using FGrid."""
    
    def __init__(self):
        self.active_focus_id: Optional[str] = None

    def set_active_focus(self, entity_id: str) -> None:
        self.active_focus_id = entity_id
        # Also mark the entity's importance temporarily or tag it
        entity = fgrid_graph.get_entity(entity_id)
        if entity:
            entity.tags = list(set(entity.tags + ["active_focus"]))
            fgrid_graph.add_entity(entity)

    def get_active_focus(self) -> Optional[Entity]:
        if not self.active_focus_id:
            return None
        return fgrid_graph.get_entity(self.active_focus_id)

    def add_interaction(self, user_prompt: str, assistant_response: str) -> str:
        """Stores a conversation step as an Entity and links it to MoStar and Mo."""
        interaction_id = f"interaction.{int(fgrid_graph.get_entity('mostar.ai').created.timestamp()) + len(fgrid_graph.entities)}"
        
        interaction_entity = Entity(
            id=interaction_id,
            type="Interaction",
            title=f"Interaction: {user_prompt[:30]}...",
            owner="Mo",
            tags=["Interaction", "WorkingMemory"],
            metadata={
                "prompt": user_prompt,
                "response": assistant_response
            }
        )
        fgrid_graph.add_entity(interaction_entity)

        # Link to Mo (the creator/user)
        fgrid_graph.add_relationship(Relationship(
            source_id="person.mo",
            target_id=interaction_id,
            relation_type="initiated"
        ))

        # Link to MoStar
        fgrid_graph.add_relationship(Relationship(
            source_id="mostar.ai",
            target_id=interaction_id,
            relation_type="participated_in"
        ))

        return interaction_id
