from typing import List
from core.fgrid.models import Entity, Relationship
from core.fgrid.graph import fgrid_graph

class ProjectMemory:
    """Manages projects, repositories, tasks, and their graph dependencies."""
    
    def create_project(self, project_id: str, title: str, description: str) -> Entity:
        project = Entity(
            id=f"project.{project_id}",
            type="Project",
            title=title,
            owner="Mo",
            tags=["Project", "Development"],
            metadata={"description": description}
        )
        fgrid_graph.add_entity(project)
        
        # Link project to user Mo
        fgrid_graph.add_relationship(Relationship(
            source_id="person.mo",
            target_id=f"project.{project_id}",
            relation_type="owns"
        ))
        
        return project

    def create_task(self, task_id: str, title: str, project_id: str) -> Entity:
        task = Entity(
            id=f"task.{task_id}",
            type="Task",
            title=title,
            owner="Mo",
            tags=["Task", "Active"],
            metadata={"status": "Pending"}
        )
        fgrid_graph.add_entity(task)

        # Link Task to Project
        fgrid_graph.add_relationship(Relationship(
            source_id=f"project.{project_id}",
            target_id=f"task.{task_id}",
            relation_type="contains_task"
        ))

        return task

    def get_project_tasks(self, project_id: str) -> List[Entity]:
        """Traverse FGrid to retrieve all tasks belonging to a project."""
        neighbors = fgrid_graph.get_neighbors(f"project.{project_id}", relation_type="contains_task")
        return [entity for entity, _ in neighbors]
