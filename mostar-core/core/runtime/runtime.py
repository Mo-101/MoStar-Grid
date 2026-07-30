import asyncio
from typing import Dict, Any, List, Optional
from core.fgrid.models import MoStarEntity, Relationship
from core.fgrid.graph import fgrid_graph
from core.soul.identity import get_mostar_identity
from core.soul.mission import get_mission_entity
from core.soul.values import get_values_entities
from services.personas.manager import PersonaManager
from services.memory.working import WorkingMemory
from services.memory.personal import PersonalMemory
from services.memory.project import ProjectMemory
from services.memory.vault import VaultMemory
from services.planner.planner import GraphPlanner

class MoStarRuntime:
    """The Executive Cortex event loop and state orchestrator for MoStar."""
    
    def __init__(self):
        self.persona_mgr = PersonaManager()
        self.working_mem = WorkingMemory()
        self.personal_mem = PersonalMemory()
        self.project_mgr = ProjectMemory()
        self.vault = VaultMemory()
        self.planner = GraphPlanner()
        self.active = False

    def bootstrap(self) -> None:
        """Register soul nodes, personas, and the user entity into the graph."""
        # 1. MoStar canonical self-identity
        mostar = get_mostar_identity()
        fgrid_graph.add_entity(mostar)

        # 2. Mission
        mission = get_mission_entity()
        fgrid_graph.add_entity(mission)
        fgrid_graph.add_relationship(Relationship(
            source_id="mostar.ai",
            target_id="soul.mission",
            relation_type="pursues"
        ))

        # 3. Values
        for val in get_values_entities():
            fgrid_graph.add_entity(val)
            fgrid_graph.add_relationship(Relationship(
                source_id="mostar.ai",
                target_id=val.id,
                relation_type="guided_by"
            ))

        # 4. Personas
        for persona_ent in self.persona_mgr.to_fgrid_entities():
            fgrid_graph.add_entity(persona_ent)
            fgrid_graph.add_relationship(Relationship(
                source_id="mostar.ai",
                target_id=persona_ent.id,
                relation_type="possesses_persona"
            ))

        # 5. User
        self.personal_mem.bootstrap_user()
        
        # Mark working memory focus to self
        self.working_mem.set_active_focus("mostar.ai")

    async def execute_user_command(self, prompt: str, target_persona: str = "prime") -> Dict[str, Any]:
        """High-level processing pipeline executing a command under a specific persona."""
        persona = self.persona_mgr.get_persona(target_persona)
        if not persona:
            return {"error": f"Persona '{target_persona}' not found."}

        # Simulated response using the persona context
        instructions = persona.get("instructions", "")
        response_text = f"[{persona['name']}] Received command: '{prompt}'. Executing with guidelines: {instructions[:60]}..."

        # Update MoStar cognition state focus
        mostar = fgrid_graph.get_entity("mostar.ai")
        if mostar and isinstance(mostar, MoStarEntity):
            mostar.cognition.current_focus = f"Processing command: {prompt[:30]}"
            if persona["name"] not in mostar.cognition.active_personas:
                mostar.cognition.active_personas = [persona["name"]]
            fgrid_graph.add_entity(mostar)

        # Record interaction in working memory
        interaction_id = self.working_mem.add_interaction(prompt, response_text)

        return {
            "persona": persona["name"],
            "response": response_text,
            "interaction_id": interaction_id
        }

    async def tick(self) -> List[str]:
        """A single iteration of the Executive Cortex scanning and advancing goals/tasks."""
        actions_taken = []
        
        # Query for all active tasks
        tasks = fgrid_graph.find_entities_by_type("Task")
        for task in tasks:
            if task.metadata.get("status") == "Pending":
                task.metadata["status"] = "Planning"
                fgrid_graph.add_entity(task)
                
                # Auto-formulate a simulated plan
                self.planner.create_plan_for_task(
                    task_id=task.id,
                    steps=["Investigate codebase", "Design solution", "Deploy and verify"]
                )
                actions_taken.append(f"Formulated plan for task: {task.id}")
                
            elif task.metadata.get("status") == "Planning":
                next_step = self.planner.advance_plan(task.id)
                if next_step:
                    actions_taken.append(f"Executing step for task {task.id}: {next_step}")
                else:
                    task.metadata["status"] = "Completed"
                    fgrid_graph.add_entity(task)
                    actions_taken.append(f"Completed task: {task.id}")

        return actions_taken

    async def run_loop(self, interval_seconds: float = 5.0) -> None:
        """Runs the background Executive Cortex tick loop."""
        self.active = True
        while self.active:
            await self.tick()
            await asyncio.sleep(interval_seconds)

    def stop(self) -> None:
        self.active = False
