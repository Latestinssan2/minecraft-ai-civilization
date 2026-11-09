"""Message bus helpers."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.database import Database
from app.models import new_id, now_iso


class MessageBus:
    def __init__(self, db: Database):
        self.db = db

    def send(self, sender: str, receiver: str, content: str, context: Optional[str] = None,
             project_id: Optional[str] = None, conversation_id: Optional[str] = None) -> Dict[str, Any]:
        conv_id = conversation_id or (f"conv_{sender}_{receiver}" if receiver not in ("broadcast",) else "conv_broadcast")
        participants = [sender] if receiver == "broadcast" else [sender, receiver]
        self.db.upsert_conversation(conv_id, participants, topic=context)
        msg = {
            "message_id": new_id("msg"),
            "conversation_id": conv_id,
            "sender": sender,
            "receiver": receiver,
            "content": content,
            "context": context,
            "project_id": project_id,
            "timestamp": now_iso(),
        }
        self.db.add_message(msg)
        return msg

    def recent(self, agent_id: Optional[str] = None, conversation_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        rows = self.db.get_messages(agent_id=agent_id, conversation_id=conversation_id, limit=limit)
        return list(reversed(rows))

    def conversations(self) -> List[Dict[str, Any]]:
        # distinct conversation ids from messages
        msgs = self.db.get_messages(limit=1000)
        seen = set()
        out = []
        for m in msgs:
            if m["conversation_id"] in seen:
                continue
            seen.add(m["conversation_id"])
            out.append({"conversation_id": m["conversation_id"], "last_message": m["content"], "timestamp": m["timestamp"]})
        return out
