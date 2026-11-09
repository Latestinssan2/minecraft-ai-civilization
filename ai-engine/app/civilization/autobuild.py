"""Automatically mine required blocks and build from a template."""
from __future__ import annotations

from typing import Any, Dict, List

from app.database import Database
from app.models import new_id


class AutoBuildManager:
    def __init__(self, db: Database):
        self.db = db

    def plan(self, project_id: str, agent_id: str, template_requirements: Dict[str, int]) -> List[str]:
        action_ids = []
        # queue automine for each required resource
        for res, amt in template_requirements.items():
            aid = new_id("action")
            self.db.add_action({
                "action_id": aid, "agent_id": agent_id, "action": "automine",
                "parameters": {"resource": res, "amount": amt}, "status": "queued",
            })
            action_ids.append(aid)
        # queue build action
        bid = new_id("action")
        self.db.add_action({
            "action_id": bid, "agent_id": agent_id, "action": "build_template",
            "parameters": {"project_id": project_id}, "status": "queued",
        })
        action_ids.append(bid)
        return action_ids
