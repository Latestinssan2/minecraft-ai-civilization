"""Settlement discovery and management."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.database import Database
from app.models import new_id, now_iso


class SettlementManager:
    def __init__(self, db: Database):
        self.db = db

    def found(self, name: str, location: Dict[str, Any], founded_by: str) -> Dict[str, Any]:
        # store as a project-like historical event + memory via caller
        sid = new_id("settle")
        self.db.add_event("settlement_founded", f"Settlement '{name}' founded at {location}",
                          related_agents=[founded_by])
        return {"settlement_id": sid, "name": name, "location": location, "founded_by": founded_by, "created_at": now_iso()}

    def assign_job(self, agent_id: str, job: str):
        self.db.add_event("job_assigned", f"{agent_id} assigned job: {job}", related_agents=[agent_id])
