"""Resource ledger / trading helpers."""
from __future__ import annotations

from typing import Any, Dict

from app.database import Database
from app.models import now_iso


class Economy:
    def __init__(self, db: Database):
        self.db = db

    def record(self, resource: str, amount: int, agent_id: str = None, reason: str = ""):
        with self.db._lock:
            self.db.conn.execute(
                "INSERT INTO resource_ledger (agent_id,resource,amount,reason,timestamp) VALUES (?,?,?,?,?)",
                (agent_id, resource, amount, reason, now_iso()))
            self.db.conn.commit()

    def transfer(self, resource: str, amount: int, from_agent: str, to_agent: str, reason: str = "trade"):
        self.record(resource, -amount, from_agent, reason)
        self.record(resource, amount, to_agent, reason)

    def balance(self, agent_id: str, resource: str) -> int:
        with self.db._lock:
            r = self.db.conn.execute(
                "SELECT COALESCE(SUM(amount),0) FROM resource_ledger WHERE agent_id=? AND resource=?",
                (agent_id, resource)).fetchone()
            return int(r[0]) if r else 0
