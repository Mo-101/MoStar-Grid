from typing import List, Dict, Any, Optional
from core.fgrid.models import Entity, Relationship
from core.fgrid.graph import fgrid_graph

class GraphPlanner:
    """A graph-native planner that traverses the FGrid to build execution plans."""
    
    def create_plan_for_task(self, task_id: str, steps: List[str]) -> Entity:
        """Creates a Plan entity in the FGrid, linked to the given task."""
        plan_id = f"plan.{task_id.replace('task.', '')}"
        
        plan_entity = Entity(
            id=plan_id,
            type="Plan",
            title=f"Plan for {task_id}",
            owner="System",
            tags=["Planner", "ExecutionPlan"],
            metadata={
                "steps": steps,
                "current_step_index": 0,
                "status": "Not Started"
            }
        )
        fgrid_graph.add_entity(plan_entity)

        # Link Task -> Plan
        fgrid_graph.add_relationship(Relationship(
            source_id=task_id,
            target_id=plan_id,
            relation_type="has_plan"
        ))

        return plan_entity

    def advance_plan(self, task_id: str) -> Optional[str]:
        """Advances the plan to the next step and returns it, or None if completed."""
        plan_id = f"plan.{task_id.replace('task.', '')}"
        plan = fgrid_graph.get_entity(plan_id)
        if not plan:
            return None

        steps = plan.metadata.get("steps", [])
        curr_idx = plan.metadata.get("current_step_index", 0)

        if curr_idx >= len(steps):
            plan.metadata["status"] = "Completed"
            fgrid_graph.add_entity(plan)
            return None

        next_step = steps[curr_idx]
        plan.metadata["current_step_index"] = curr_idx + 1
        plan.metadata["status"] = "In Progress"
        fgrid_graph.add_entity(plan)
        return next_step

    def get_plan_context(self, task_id: str) -> Dict[str, Any]:
        """Traverses the graph around the task to gather relevant planning context."""
        context = {
            "task": fgrid_graph.get_entity(task_id),
            "project": None,
            "dependencies": []
        }

        # Find project this task belongs to
        relationships = fgrid_graph.get_relationships(task_id)
        for r in relationships:
            if r.relation_type == "contains_task" and r.target_id == task_id:
                context["project"] = fgrid_graph.get_entity(r.source_id)

        # Find dependencies of the task/project
        neighbors = fgrid_graph.get_neighbors(task_id, relation_type="depends_on")
        for entity, _ in neighbors:
            context["dependencies"].append(entity)

        return context
