from typing import Optional
from core.fgrid.models import Entity, Relationship
from core.fgrid.graph import fgrid_graph

class PersonalMemory:
    """Manages profile details, preferences, and social relationships surrounding user 'Mo'."""
    
    def bootstrap_user(self) -> None:
        """Bootstraps the main user 'Mo' in the graph if not exists."""
        mo = Entity(
            id="person.mo",
            type="Person",
            title="Mo",
            owner="Mo",
            tags=["Creator", "User"],
            metadata={
                "role": "Lead Architect",
                "organization": "MoStar Industries"
            }
        )
        fgrid_graph.add_entity(mo)

        # Build relationship: Mo creator_of MoStar
        fgrid_graph.add_relationship(Relationship(
            source_id="person.mo",
            target_id="mostar.ai",
            relation_type="creator_of"
        ))

    def get_user_profile(self) -> Optional[Entity]:
        return fgrid_graph.get_entity("person.mo")

    def update_preference(self, key: str, value: str) -> None:
        user = self.get_user_profile()
        if user:
            if "preferences" not in user.metadata:
                user.metadata["preferences"] = {}
            user.metadata["preferences"][key] = value
            fgrid_graph.add_entity(user)
