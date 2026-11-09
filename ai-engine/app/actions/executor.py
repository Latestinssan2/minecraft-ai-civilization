"""Action execution worker."""
from __future__ import annotations

import threading
import time
from typing import Any, Dict, List, Optional

from app.database import Database
from app.world.bridge import WorldBridge


class ActionExecutor:
    def __init__(self, db: Database, bridge: WorldBridge, poll_interval: float = 1.0):
        self.db = db
        self.bridge = bridge
        self.poll_interval = poll_interval
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def start(self):
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=5)

    def _loop(self):
        while not self._stop.is_set():
            try:
                queued = self.db.list_actions(status="queued", limit=50)
                for a in queued:
                    self._execute_one(a)
            except Exception:
                pass
            self._stop.wait(self.poll_interval)

    def _execute_one(self, a: Dict[str, Any]):
        aid = a["action_id"]
        # prevent duplicate execution: mark running
        self.db.update_action(aid, status="running")
        try:
            res = self.bridge.execute_action(a["agent_id"], a["action"], a.get("parameters", {}))
            ok = bool(res.get("success", True))
            status = "succeeded" if ok else "failed"
            self.db.update_action(aid, status=status, result=res, completed_at=__import__("app.models", fromlist=["now_iso"]).now_iso())
            self.db.add_action_result(aid, status, result=res, error=None if ok else res.get("error"))
            # add memory of action
            from app.agents.agent import Agent  # noqa
        except Exception as e:
            self.db.update_action(aid, status="failed", error=str(e), completed_at=__import__("app.models", fromlist=["now_iso"]).now_iso())
            self.db.add_action_result(aid, "failed", error=str(e))
