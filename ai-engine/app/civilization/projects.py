"""Project management helpers."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.database import Database
from app.models import Project, new_id, now_iso


class ProjectManager:
    def __init__(self, db: Database):
        self.db = db

    def create(self, name: str, proposed_by: str, description: str = "", requirements: Optional[Dict[str, int]] = None,
               assigned_agents: Optional[List[str]] = None) -> Dict[str, Any]:
        proj = Project(
            project_id=new_id("proj"),
            name=name,
            proposed_by=proposed_by,
            description=description,
            requirements=requirements or {},
            assigned_agents=assigned_agents or [],
        )
        self.db.add_project(proj.to_dict())
        self.db.add_event("project_created", f"Project '{name}' proposed by {proposed_by}",
                          related_agents=[proposed_by], related_project=proj.project_id)
        return proj.to_dict()

    def get(self, project_id: str) -> Optional[Dict[str, Any]]:
        return self.db.get_project(project_id)

    def list(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        return self.db.list_projects(status=status)

    def join(self, project_id: str, agent_id: str, role: str = "member"):
        self.db.join_project(project_id, agent_id, role)
        proj = self.db.get_project(project_id)
        if proj and agent_id not in proj["assigned_agents"]:
            agents = list(proj["assigned_agents"]) + [agent_id]
            self.db.update_project(project_id, assigned_agents=agents)
        self.db.add_event("project_join", f"{agent_id} joined project {project_id}", related_agents=[agent_id], related_project=project_id)

    def update_progress(self, project_id: str, progress: Dict[str, int]):
        self.db.update_project(project_id, progress=progress)
        proj = self.db.get_project(project_id)
        if proj:
            req = proj.get("requirements", {}) or {}
            if req and all(progress.get(k, 0) >= v for k, v in req.items()):
                self.db.update_project(project_id, status="completed")
                self.db.add_event("project_completed", f"Project '{proj['name']}' completed",
                                  related_agents=proj.get("assigned_agents", []), related_project=project_id)

    def set_status(self, project_id: str, status: str):
        self.db.update_project(project_id, status=status)
