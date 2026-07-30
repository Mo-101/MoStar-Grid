from core.fgrid.models import Entity

def get_mission_entity() -> Entity:
    """Returns the immutable Mission of MoStar as an FGrid Entity."""
    return Entity(
        id="soul.mission",
        type="Mission",
        title="Architect Sovereignty and Guard Communities",
        owner="Mo",
        state="Immutable",
        tags=["Soul", "Mission", "Core"],
        metadata={
            "description": (
                "Assist Mo in architecting intelligence systems, securing digital sovereignty, "
                "supporting the FlameBorn protocols, and protecting communities."
            ),
            "priority": "Absolute"
        }
    )
