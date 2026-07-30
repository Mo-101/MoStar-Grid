import os
import yaml
from typing import Dict, Any, List, Optional
from core.fgrid.models import Entity

class PersonaManager:
    """Manages MoStar personas, loading them from configurations and registering them in FGrid."""
    
    def __init__(self, personas_dir: Optional[str] = None):
        if personas_dir is None:
            # Default to the sibling personas/ directory
            personas_dir = os.path.join(os.path.dirname(__file__), "personas")
        self.personas_dir = personas_dir
        self.personas: Dict[str, Dict[str, Any]] = {}
        self.load_personas()

    def load_personas(self) -> None:
        """Loads all YAML configurations from the personas directory."""
        if not os.path.exists(self.personas_dir):
            return
        for file in os.listdir(self.personas_dir):
            if file.endswith(".yaml") or file.endswith(".yml"):
                name = os.path.splitext(file)[0].lower()
                path = os.path.join(self.personas_dir, file)
                with open(path, "r", encoding="utf-8") as f:
                    try:
                        data = yaml.safe_load(f)
                        if data:
                            self.personas[name] = data
                    except Exception as e:
                        print(f"Error loading persona {file}: {e}")

    def list_personas(self) -> List[str]:
        return list(self.personas.keys())

    def get_persona(self, name: str) -> Optional[Dict[str, Any]]:
        return self.personas.get(name.lower())

    def to_fgrid_entities(self) -> List[Entity]:
        """Converts loaded personas into FGrid Entities."""
        entities = []
        for name, data in self.personas.items():
            entities.append(
                Entity(
                    id=f"persona.{name}",
                    type="Persona",
                    title=data.get("name", name.capitalize()),
                    owner="System",
                    state="Active",
                    tags=["Persona", "Cognition"],
                    metadata={
                        "voice": data.get("voice"),
                        "humor": data.get("humor"),
                        "description": data.get("description"),
                        "instructions": data.get("instructions"),
                        "preferred_tools": data.get("preferred_tools", [])
                    }
                )
            )
        return entities
