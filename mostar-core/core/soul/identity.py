from core.fgrid.models import MoStarEntity, CognitionState
from core.soul.version import VERSION, CODENAME

def get_mostar_identity() -> MoStarEntity:
    """Returns the canonical MoStar AI Companion entity representation."""
    return MoStarEntity(
        id="mostar.ai",
        title="MoStar AI",
        owner="Mo",
        version=CODENAME,
        state="Alive",
        tags=["Companion", "Core", "Kernel"],
        cognition=CognitionState(
            current_focus="Bootstrapping System",
            active_personas=["Prime"],
            runtime_health="Healthy"
        ),
        active_tasks=[],
        active_projects=["FlameBorn"],
        memory_layers=["working", "personal", "project", "vault"],
        capabilities=["Planner", "TruthEngine", "LogicCodex"],
        connected_tools=["Terminal", "FileViewer"]
    )
