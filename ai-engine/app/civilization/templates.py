"""Pre-built structure templates with block requirements and relative layouts."""
from __future__ import annotations

from typing import Any, Dict, List

TEMPLATES = {
    "farm": {
        "name": "Farm",
        "description": "Small wheat farm with water.",
        "requirements": {"dirt": 20, "water_bucket": 1, "wheat_seeds": 20, "oak_fence": 10},
        "blocks": [
            {"rel": [0, 0, 0], "block": "farmland"},
            {"rel": [1, 0, 0], "block": "farmland"},
        ],
    },
    "house": {
        "name": "House",
        "description": "Small wooden house.",
        "requirements": {"oak_planks": 60, "oak_log": 20, "glass_pane": 8, "oak_door": 1, "torch": 4},
        "blocks": [],
    },
    "kingdom": {
        "name": "Kingdom",
        "description": "Large settlement with walls and tower.",
        "requirements": {"stone_bricks": 500, "oak_planks": 200, "torch": 50, "iron_door": 4, "glass": 30},
        "blocks": [],
    },
    "tower": {
        "name": "Watchtower",
        "description": "Defensive tower.",
        "requirements": {"cobblestone": 120, "oak_fence": 20, "torch": 8},
        "blocks": [],
    },
}


class TemplateManager:
    def __init__(self):
        self.templates = TEMPLATES

    def list(self) -> List[Dict[str, Any]]:
        out = []
        for tid, t in self.templates.items():
            out.append({"template_id": tid, "name": t["name"], "description": t["description"],
                        "requirements": t["requirements"]})
        return out

    def get(self, tid: str) -> Dict[str, Any]:
        t = self.templates.get(tid)
        if not t:
            return {}
        return {"template_id": tid, **t}

    def create_project(self, db, proposed_by: str, template_id: str, origin: Dict[str, int] = None) -> Dict[str, Any]:
        from app.civilization.projects import ProjectManager
        t = self.get(template_id)
        if not t:
            return {}
        pm = ProjectManager(db)
        proj = pm.create(name=t["name"], proposed_by=proposed_by, description=t["description"],
                         requirements=dict(t["requirements"]), assigned_agents=[proposed_by])
        return proj
