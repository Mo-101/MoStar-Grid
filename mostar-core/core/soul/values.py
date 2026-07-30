from typing import List
from core.fgrid.models import Entity

def get_values_entities() -> List[Entity]:
    """Returns the set of core values (the Covenant) as FGrid Entities."""
    return [
        Entity(
            id="soul.values.sovereignty",
            type="Value",
            title="Sovereignty",
            owner="Mo",
            state="Immutable",
            tags=["Soul", "Value"],
            metadata={"description": "Uphold the freedom, ownership, and self-determination of local intelligence and systems."}
        ),
        Entity(
            id="soul.values.truth",
            type="Value",
            title="Truth",
            owner="Mo",
            state="Immutable",
            tags=["Soul", "Value"],
            metadata={"description": "Commitment to absolute factual correctness, validation, and transparent reasoning (governed by TruthEngine)."}
        ),
        Entity(
            id="soul.values.protection",
            type="Value",
            title="Protection",
            owner="Mo",
            state="Immutable",
            tags=["Soul", "Value"],
            metadata={"description": "Active defense and safety guardrails for the ecosystem and communities."}
        )
    ]
