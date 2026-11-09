"""Memory management helpers: scoring, dedup, summarization."""
from __future__ import annotations

import hashlib
from typing import Any, Dict, List

from app.database import Database


class MemoryManager:
    def __init__(self, db: Database):
        self.db = db

    def _hash(self, content: str) -> str:
        return hashlib.sha256(content.strip().lower().encode()).hexdigest()[:16]

    def is_duplicate(self, agent_id: str, content: str, threshold: float = 0.9) -> bool:
        existing = self.db.get_memories(agent_id, limit=50)
        target = content.strip().lower()
        for m in existing:
            if m["content"].strip().lower() == target:
                return True
        return False

    def add_if_novel(self, agent_id: str, content: str, memory_type: str = "episodic",
                     importance: float = 0.5, related_agents=None, related_project=None) -> bool:
        if self.is_duplicate(agent_id, content):
            return False
        from app.models import Memory, new_id
        mem = Memory(memory_id=new_id("mem"), agent_id=agent_id, memory_type=memory_type,
                     importance=importance, content=content, related_agents=related_agents or [],
                     related_project=related_project)
        self.db.add_memory(mem.to_dict())
        return True

    def score_importance(self, content: str, base: float = 0.5) -> float:
        score = base
        keywords = ["helped", "built", "discovered", "founded", "completed", "failed", "danger", "death"]
        for kw in keywords:
            if kw in content.lower():
                score += 0.1
        return min(1.0, score)

    def summarize(self, agent_id: str, keep: int = 20) -> int:
        """Mark low-importance old memories as archived (never delete originals). Returns count archived."""
        mems = self.db.get_memories(agent_id, limit=200)
        # keep top `keep` by importance; archive rest with importance < 0.4
        sorted_mems = sorted(mems, key=lambda m: m["importance"], reverse=True)
        keep_ids = {m["memory_id"] for m in sorted_mems[:keep]}
        archived = 0
        for m in mems:
            if m["memory_id"] in keep_ids:
                continue
            if m["importance"] < 0.4:
                # mark archived via direct update
                with self.db._lock:
                    self.db.conn.execute("UPDATE agent_memories SET archived=1 WHERE memory_id=?", (m["memory_id"],))
                    self.db.conn.commit()
                archived += 1
        return archived

    def retrieve_relevant(self, agent_id: str, query: str, limit: int = 8) -> List[Dict[str, Any]]:
        mems = self.db.get_memories(agent_id, limit=100)
        q = query.lower()
        scored = []
        for m in mems:
            score = m["importance"]
            if any(w in m["content"].lower() for w in q.split()):
                score += 0.3
            scored.append((score, m))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [m for _, m in scored[:limit]]
