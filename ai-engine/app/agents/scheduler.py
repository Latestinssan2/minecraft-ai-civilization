"""Event-driven + staggered decision scheduler for agents."""
from __future__ import annotations

import threading
import time
from typing import Callable, Dict, List, Optional

from app.agents.agent import Agent


class AgentScheduler:
    def __init__(self, agents: List[Agent], interval_seconds: int = 120, concurrency: int = 1,
                 on_decision: Optional[Callable[[Agent, object], None]] = None):
        self.agents = {a.agent_id: a for a in agents}
        self.agent_list = agents
        self.interval = interval_seconds
        self.concurrency = max(1, concurrency)
        self.on_decision = on_decision
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Semaphore(self.concurrency)
        self._pending: List[str] = []
        self._pending_lock = threading.Lock()

    def start(self):
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=5)

    def trigger(self, agent_id: str, reason: str = "event"):
        with self._pending_lock:
            if agent_id not in self._pending:
                self._pending.append(agent_id)
        # store reason on agent as alert if not set
        ag = self.agents.get(agent_id)
        if ag and not ag.state.alert:
            ag.state.alert = reason

    def trigger_all(self, reason: str = "event"):
        for aid in self.agents:
            self.trigger(aid, reason)

    def run_once(self):
        for aid in list(self.agents.keys()):
            self._run_one(self.agents[aid])

    def _loop(self):
        while not self._stop.is_set():
            # process pending event triggers first
            with self._pending_lock:
                pending = list(self._pending)
                self._pending.clear()
            for aid in pending:
                ag = self.agents.get(aid)
                if ag:
                    self._run_one(ag)
                    time.sleep(0.5)
            # periodic fallback
            self._stop.wait(self.interval)
            if not self._stop.is_set():
                # staggered: run one agent per interval slice
                pass

    def _run_one(self, agent: Agent):
        def task():
            with self._lock:
                try:
                    agent.state.current_activity = "thinking"
                    agent.persist()
                    dec = agent.decide()
                    if dec is not None:
                        agent.state.current_activity = "acting"
                        agent.state.thoughts = dec.thoughts
                        agent.state.intention = dec.intention
                        agent.persist()
                        if self.on_decision:
                            self.on_decision(agent, dec)
                except Exception as e:
                    agent.state.current_activity = "error"
                    agent.state.status = "error"
                    agent.persist()
                finally:
                    if agent.state.current_activity in ("thinking", "acting"):
                        agent.state.current_activity = "idle"
                        agent.persist()
        t = threading.Thread(target=task, daemon=True)
        t.start()