"""SQLite persistence layer."""
from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.models import now_iso


SCHEMA = r"""
CREATE TABLE IF NOT EXISTS agents (
    agent_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    personality TEXT NOT NULL,
    interests TEXT NOT NULL DEFAULT '[]',
    current_goal TEXT DEFAULT '',
    current_activity TEXT DEFAULT 'idle',
    position TEXT DEFAULT '{}',
    health REAL DEFAULT 20.0,
    inventory TEXT DEFAULT '{}',
    status TEXT DEFAULT 'active',
    last_decision_at TEXT,
    last_message TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS agent_personalities (
    agent_id TEXT PRIMARY KEY,
    personality TEXT NOT NULL,
    interests TEXT NOT NULL DEFAULT '[]',
    FOREIGN KEY(agent_id) REFERENCES agents(agent_id)
);

CREATE TABLE IF NOT EXISTS agent_goals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT NOT NULL,
    goal TEXT NOT NULL,
    priority TEXT DEFAULT 'medium',
    status TEXT DEFAULT 'active',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(agent_id) REFERENCES agents(agent_id)
);

CREATE TABLE IF NOT EXISTS agent_memories (
    memory_id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    memory_type TEXT NOT NULL,
    importance REAL DEFAULT 0.5,
    content TEXT NOT NULL,
    related_agents TEXT DEFAULT '[]',
    related_project TEXT,
    timestamp TEXT NOT NULL,
    summary TEXT,
    archived INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS messages (
    message_id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL,
    sender TEXT NOT NULL,
    receiver TEXT NOT NULL,
    content TEXT NOT NULL,
    context TEXT,
    project_id TEXT,
    timestamp TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS conversations (
    conversation_id TEXT PRIMARY KEY,
    participants TEXT NOT NULL,
    topic TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS actions (
    action_id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    action TEXT NOT NULL,
    parameters TEXT DEFAULT '{}',
    status TEXT DEFAULT 'queued',
    result TEXT,
    error TEXT,
    created_at TEXT NOT NULL,
    completed_at TEXT,
    retries INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS action_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action_id TEXT NOT NULL,
    status TEXT NOT NULL,
    result TEXT,
    error TEXT,
    timestamp TEXT NOT NULL,
    FOREIGN KEY(action_id) REFERENCES actions(action_id)
);

CREATE TABLE IF NOT EXISTS decisions (
    decision_id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    current_goal TEXT,
    reasoning_summary TEXT,
    plan TEXT DEFAULT '[]',
    priority TEXT DEFAULT 'medium',
    actions TEXT DEFAULT '[]',
    timestamp TEXT NOT NULL,
    provider_latency_ms INTEGER
);

CREATE TABLE IF NOT EXISTS relationships (
    agent_a TEXT NOT NULL,
    agent_b TEXT NOT NULL,
    trust REAL DEFAULT 0.5,
    familiarity REAL DEFAULT 0.0,
    notes TEXT DEFAULT '',
    updated_at TEXT NOT NULL,
    PRIMARY KEY (agent_a, agent_b)
);

CREATE TABLE IF NOT EXISTS civilizations (
    civilization_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    metadata TEXT DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS projects (
    project_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    proposed_by TEXT NOT NULL,
    description TEXT DEFAULT '',
    requirements TEXT DEFAULT '{}',
    progress TEXT DEFAULT '{}',
    assigned_agents TEXT DEFAULT '[]',
    status TEXT DEFAULT 'planning',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS project_members (
    project_id TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    role TEXT DEFAULT 'member',
    joined_at TEXT NOT NULL,
    PRIMARY KEY (project_id, agent_id)
);

CREATE TABLE IF NOT EXISTS world_observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT NOT NULL,
    observation TEXT NOT NULL,
    timestamp TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS historical_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    description TEXT NOT NULL,
    related_agents TEXT DEFAULT '[]',
    related_project TEXT,
    timestamp TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS agent_profiles (
    profile_id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    name TEXT NOT NULL,
    personality TEXT NOT NULL,
    interests TEXT NOT NULL DEFAULT '[]',
    skin TEXT DEFAULT '',
    memory_snapshot TEXT DEFAULT '[]',
    created_at TEXT NOT NULL,
    is_default INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS resource_ledger (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT,
    resource TEXT NOT NULL,
    amount INTEGER NOT NULL,
    reason TEXT,
    timestamp TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS llm_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT,
    provider TEXT,
    model TEXT,
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    latency_ms INTEGER,
    status TEXT,
    timestamp TEXT NOT NULL
);
"""


class Database:
    def __init__(self, path: str):
        self.path = path
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self):
        with self._lock:
            self.conn.executescript(SCHEMA)
            # migrations for new columns
            cols = {r[1] for r in self.conn.execute("PRAGMA table_info(agents)").fetchall()}
            dcols = {r[1] for r in self.conn.execute("PRAGMA table_info(decisions)").fetchall()}
            for col, decl in (("skin", "TEXT DEFAULT ''"), ("profile_name", "TEXT DEFAULT 'default'")):
                if col not in cols:
                    self.conn.execute(f"ALTER TABLE agents ADD COLUMN {col} {decl}")
            for col, decl in (("intention", "TEXT DEFAULT ''"), ("thoughts", "TEXT DEFAULT ''")):
                if col not in dcols:
                    self.conn.execute(f"ALTER TABLE decisions ADD COLUMN {col} {decl}")
            for col, decl in (("hunger", "REAL DEFAULT 20.0"), ("intention", "TEXT DEFAULT ''"),
                              ("thoughts", "TEXT DEFAULT ''"), ("alert", "TEXT"), ("hotbar_slot", "INTEGER DEFAULT 0")):
                if col not in cols:
                    self.conn.execute(f"ALTER TABLE agents ADD COLUMN {col} {decl}")
            self.conn.commit()

    def close(self):
        with self._lock:
            self.conn.close()

    # --- agents ---
    def upsert_agent(self, agent_id, name, personality, interests, state=None):
        state = state or {}
        now = now_iso()
        with self._lock:
            self.conn.execute(
                """INSERT INTO agents (agent_id,name,personality,interests,current_goal,current_activity,intention,thoughts,position,health,hunger,inventory,hotbar_slot,skin,profile_name,status,last_decision_at,last_message,alert,created_at,updated_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                   ON CONFLICT(agent_id) DO UPDATE SET
                     name=excluded.name, personality=excluded.personality, interests=excluded.interests,
                     current_goal=excluded.current_goal, current_activity=excluded.current_activity,
                     intention=excluded.intention, thoughts=excluded.thoughts,
                     position=excluded.position, health=excluded.health, hunger=excluded.hunger,
                     inventory=excluded.inventory, hotbar_slot=excluded.hotbar_slot,
                     skin=excluded.skin, profile_name=excluded.profile_name,
                     status=excluded.status, last_decision_at=excluded.last_decision_at,
                     last_message=excluded.last_message, alert=excluded.alert, updated_at=excluded.updated_at""",
                (agent_id, name, personality, json.dumps(interests),
                 state.get("current_goal", ""), state.get("current_activity", "idle"),
                 state.get("intention", ""), state.get("thoughts", ""),
                 json.dumps(state.get("position", {})), state.get("health", 20.0), state.get("hunger", 20.0),
                 json.dumps(state.get("inventory", {})), state.get("hotbar_slot", 0),
                 state.get("skin", ""), state.get("profile_name", "default"),
                 state.get("status", "active"), state.get("last_decision_at"), state.get("last_message"),
                 state.get("alert"), now, now))
            self.conn.execute(
                """INSERT INTO agent_personalities (agent_id,personality,interests) VALUES (?,?,?)
                   ON CONFLICT(agent_id) DO UPDATE SET personality=excluded.personality, interests=excluded.interests""",
                (agent_id, personality, json.dumps(interests)))
            self.conn.commit()

    def get_agent(self, agent_id):
        with self._lock:
            r = self.conn.execute("SELECT * FROM agents WHERE agent_id=?", (agent_id,)).fetchone()
            if not r:
                return None
            return self._row_to_agent(r)

    def list_agents(self):
        with self._lock:
            rows = self.conn.execute("SELECT * FROM agents ORDER BY agent_id").fetchall()
            return [self._row_to_agent(r) for r in rows]

    def _row_to_agent(self, r):
        return {
            "agent_id": r["agent_id"],
            "name": r["name"],
            "personality": r["personality"],
            "interests": json.loads(r["interests"] or "[]"),
            "current_goal": r["current_goal"] or "",
            "current_activity": r["current_activity"] or "idle",
            "intention": r["intention"] or "" if "intention" in r.keys() else "",
            "thoughts": r["thoughts"] or "" if "thoughts" in r.keys() else "",
            "position": json.loads(r["position"] or "{}"),
            "health": r["health"],
            "hunger": r["hunger"] if "hunger" in r.keys() and r["hunger"] is not None else 20.0,
            "inventory": json.loads(r["inventory"] or "{}"),
            "hotbar_slot": r["hotbar_slot"] if "hotbar_slot" in r.keys() and r["hotbar_slot"] is not None else 0,
            "skin": r["skin"] if "skin" in r.keys() else "",
            "profile_name": r["profile_name"] if "profile_name" in r.keys() else "default",
            "alert": r["alert"] if "alert" in r.keys() else None,
            "status": r["status"] or "active",
            "last_decision_at": r["last_decision_at"],
            "last_message": r["last_message"],
            "created_at": r["created_at"] if "created_at" in r.keys() else None,
        }

    def update_agent_state(self, agent_id, **fields):
        allowed = {"current_goal", "current_activity", "position", "health", "inventory",
                   "status", "last_decision_at", "last_message"}
        sets = []
        vals = []
        for k, v in fields.items():
            if k not in allowed:
                continue
            if k in ("position", "inventory"):
                v = json.dumps(v)
            sets.append(f"{k}=?")
            vals.append(v)
        if not sets:
            return
        vals.append(now_iso())
        vals.append(agent_id)
        with self._lock:
            self.conn.execute(f"UPDATE agents SET {','.join(sets)}, updated_at=? WHERE agent_id=?", vals)
            self.conn.commit()

    # --- memories ---
    def add_memory(self, mem: Dict[str, Any]):
        with self._lock:
            self.conn.execute(
                """INSERT OR REPLACE INTO agent_memories
                   (memory_id,agent_id,memory_type,importance,content,related_agents,related_project,timestamp,summary,archived)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (mem["memory_id"], mem["agent_id"], mem["memory_type"], mem.get("importance", 0.5),
                 mem["content"], json.dumps(mem.get("related_agents", [])), mem.get("related_project"),
                 mem.get("timestamp", now_iso()), mem.get("summary"), 1 if mem.get("archived") else 0))
            self.conn.commit()

    def get_memories(self, agent_id, limit=50, memory_type=None, min_importance=0.0):
        q = "SELECT * FROM agent_memories WHERE agent_id=? AND archived=0"
        params = [agent_id]
        if memory_type:
            q += " AND memory_type=?"
            params.append(memory_type)
        q += " AND importance>=?"
        params.append(min_importance)
        q += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        with self._lock:
            rows = self.conn.execute(q, params).fetchall()
            return [self._row_to_memory(r) for r in rows]

    def get_shared_memories(self, limit=50):
        with self._lock:
            rows = self.conn.execute(
                "SELECT * FROM agent_memories WHERE memory_type='shared' AND archived=0 ORDER BY timestamp DESC LIMIT ?",
                (limit,)).fetchall()
            return [self._row_to_memory(r) for r in rows]

    def _row_to_memory(self, r):
        return {
            "memory_id": r["memory_id"],
            "agent_id": r["agent_id"],
            "memory_type": r["memory_type"],
            "importance": r["importance"],
            "content": r["content"],
            "related_agents": json.loads(r["related_agents"] or "[]"),
            "related_project": r["related_project"],
            "timestamp": r["timestamp"],
            "summary": r["summary"],
            "archived": bool(r["archived"]),
        }

    # --- messages ---
    def add_message(self, msg: Dict[str, Any]):
        with self._lock:
            self.conn.execute(
                """INSERT OR REPLACE INTO messages (message_id,conversation_id,sender,receiver,content,context,project_id,timestamp)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (msg["message_id"], msg["conversation_id"], msg["sender"], msg["receiver"], msg["content"],
                 msg.get("context"), msg.get("project_id"), msg.get("timestamp", now_iso())))
            self.conn.commit()

    def get_messages(self, agent_id=None, conversation_id=None, limit=100):
        q = "SELECT * FROM messages"
        params = []
        conds = []
        if agent_id:
            conds.append("(sender=? OR receiver=?)")
            params += [agent_id, agent_id]
        if conversation_id:
            conds.append("conversation_id=?")
            params.append(conversation_id)
        if conds:
            q += " WHERE " + " AND ".join(conds)
        q += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        with self._lock:
            rows = self.conn.execute(q, params).fetchall()
            return [dict(r) for r in rows]

    def upsert_conversation(self, conversation_id, participants, topic=None):
        now = now_iso()
        with self._lock:
            self.conn.execute(
                """INSERT INTO conversations (conversation_id,participants,topic,created_at,updated_at)
                   VALUES (?,?,?,?,?)
                   ON CONFLICT(conversation_id) DO UPDATE SET participants=excluded.participants, topic=excluded.topic, updated_at=excluded.updated_at""",
                (conversation_id, json.dumps(participants), topic, now, now))
            self.conn.commit()

    # --- actions ---
    def add_action(self, action: Dict[str, Any]):
        with self._lock:
            self.conn.execute(
                """INSERT OR REPLACE INTO actions (action_id,agent_id,action,parameters,status,result,error,created_at,completed_at,retries)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (action["action_id"], action["agent_id"], action["action"], json.dumps(action.get("parameters", {})),
                 action.get("status", "queued"), json.dumps(action["result"]) if action.get("result") is not None else None,
                 action.get("error"), action.get("created_at", now_iso()), action.get("completed_at"),
                 action.get("retries", 0)))
            self.conn.commit()

    def update_action(self, action_id, **fields):
        allowed = {"status", "result", "error", "completed_at", "retries"}
        sets = []
        vals = []
        for k, v in fields.items():
            if k not in allowed:
                continue
            if k == "result" and v is not None:
                v = json.dumps(v)
            sets.append(f"{k}=?")
            vals.append(v)
        if not sets:
            return
        vals.append(action_id)
        with self._lock:
            self.conn.execute(f"UPDATE actions SET {','.join(sets)} WHERE action_id=?", vals)
            self.conn.commit()

    def get_action(self, action_id):
        with self._lock:
            r = self.conn.execute("SELECT * FROM actions WHERE action_id=?", (action_id,)).fetchone()
            if not r:
                return None
            return self._row_to_action(r)

    def list_actions(self, agent_id=None, status=None, limit=100):
        q = "SELECT * FROM actions"
        params = []
        conds = []
        if agent_id:
            conds.append("agent_id=?"); params.append(agent_id)
        if status:
            conds.append("status=?"); params.append(status)
        if conds:
            q += " WHERE " + " AND ".join(conds)
        q += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        with self._lock:
            rows = self.conn.execute(q, params).fetchall()
            return [self._row_to_action(r) for r in rows]

    def _row_to_action(self, r):
        return {
            "action_id": r["action_id"],
            "agent_id": r["agent_id"],
            "action": r["action"],
            "parameters": json.loads(r["parameters"] or "{}"),
            "status": r["status"],
            "result": json.loads(r["result"]) if r["result"] else None,
            "error": r["error"],
            "created_at": r["created_at"],
            "completed_at": r["completed_at"],
            "retries": r["retries"],
        }

    def add_action_result(self, action_id, status, result=None, error=None):
        with self._lock:
            self.conn.execute(
                "INSERT INTO action_results (action_id,status,result,error,timestamp) VALUES (?,?,?,?,?)",
                (action_id, status, json.dumps(result) if result is not None else None, error, now_iso()))
            self.conn.commit()

    # --- decisions ---
    def add_decision(self, dec: Dict[str, Any]):
        with self._lock:
            self.conn.execute(
                """INSERT OR REPLACE INTO decisions (decision_id,agent_id,current_goal,reasoning_summary,intention,thoughts,plan,priority,actions,timestamp,provider_latency_ms)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (dec["decision_id"], dec["agent_id"], dec.get("current_goal"), dec.get("reasoning_summary"),
                 dec.get("intention", ""), dec.get("thoughts", ""),
                 json.dumps(dec.get("plan", [])), dec.get("priority", "medium"), json.dumps(dec.get("actions", [])),
                 dec.get("timestamp", now_iso()), dec.get("provider_latency_ms")))
            self.conn.commit()

    def get_decisions(self, agent_id=None, limit=50):
        q = "SELECT * FROM decisions"
        params = []
        if agent_id:
            q += " WHERE agent_id=?"; params.append(agent_id)
        q += " ORDER BY timestamp DESC LIMIT ?"; params.append(limit)
        with self._lock:
            rows = self.conn.execute(q, params).fetchall()
            out = []
            for r in rows:
                out.append({
                    "decision_id": r["decision_id"],
                    "agent_id": r["agent_id"],
                    "current_goal": r["current_goal"],
                    "reasoning_summary": r["reasoning_summary"],
                    "intention": r["intention"] if "intention" in r.keys() else "",
                    "thoughts": r["thoughts"] if "thoughts" in r.keys() else "",
                    "plan": json.loads(r["plan"] or "[]"),
                    "priority": r["priority"],
                    "actions": json.loads(r["actions"] or "[]"),
                    "timestamp": r["timestamp"],
                    "provider_latency_ms": r["provider_latency_ms"],
                })
            return out

    # --- relationships ---
    def upsert_relationship(self, agent_a, agent_b, trust=None, familiarity=None, notes=None):
        now = now_iso()
        existing = self.get_relationship(agent_a, agent_b)
        t = trust if trust is not None else (existing["trust"] if existing else 0.5)
        f = familiarity if familiarity is not None else (existing["familiarity"] if existing else 0.0)
        n = notes if notes is not None else (existing["notes"] if existing else "")
        with self._lock:
            self.conn.execute(
                """INSERT INTO relationships (agent_a,agent_b,trust,familiarity,notes,updated_at) VALUES (?,?,?,?,?,?)
                   ON CONFLICT(agent_a,agent_b) DO UPDATE SET trust=excluded.trust, familiarity=excluded.familiarity, notes=excluded.notes, updated_at=excluded.updated_at""",
                (agent_a, agent_b, t, f, n, now))
            self.conn.commit()

    def get_relationship(self, agent_a, agent_b):
        with self._lock:
            r = self.conn.execute("SELECT * FROM relationships WHERE agent_a=? AND agent_b=?", (agent_a, agent_b)).fetchone()
            if not r:
                return None
            return {"agent_a": r["agent_a"], "agent_b": r["agent_b"], "trust": r["trust"],
                    "familiarity": r["familiarity"], "notes": r["notes"], "updated_at": r["updated_at"]}

    def list_relationships(self, agent_id=None):
        q = "SELECT * FROM relationships"
        params = []
        if agent_id:
            q += " WHERE agent_a=? OR agent_b=?"; params += [agent_id, agent_id]
        with self._lock:
            rows = self.conn.execute(q, params).fetchall()
            return [{"agent_a": r["agent_a"], "agent_b": r["agent_b"], "trust": r["trust"],
                     "familiarity": r["familiarity"], "notes": r["notes"], "updated_at": r["updated_at"]} for r in rows]

    # --- projects ---
    def add_project(self, proj: Dict[str, Any]):
        with self._lock:
            self.conn.execute(
                """INSERT OR REPLACE INTO projects (project_id,name,proposed_by,description,requirements,progress,assigned_agents,status,created_at,updated_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (proj["project_id"], proj["name"], proj["proposed_by"], proj.get("description", ""),
                 json.dumps(proj.get("requirements", {})), json.dumps(proj.get("progress", {})),
                 json.dumps(proj.get("assigned_agents", [])), proj.get("status", "planning"),
                 proj.get("created_at", now_iso()), proj.get("updated_at", now_iso())))
            self.conn.commit()

    def get_project(self, project_id):
        with self._lock:
            r = self.conn.execute("SELECT * FROM projects WHERE project_id=?", (project_id,)).fetchone()
            if not r:
                return None
            return self._row_to_project(r)

    def list_projects(self, status=None):
        q = "SELECT * FROM projects"
        params = []
        if status:
            q += " WHERE status=?"; params.append(status)
        q += " ORDER BY created_at DESC"
        with self._lock:
            rows = self.conn.execute(q, params).fetchall()
            return [self._row_to_project(r) for r in rows]

    def _row_to_project(self, r):
        return {
            "project_id": r["project_id"],
            "name": r["name"],
            "proposed_by": r["proposed_by"],
            "description": r["description"],
            "requirements": json.loads(r["requirements"] or "{}"),
            "progress": json.loads(r["progress"] or "{}"),
            "assigned_agents": json.loads(r["assigned_agents"] or "[]"),
            "status": r["status"],
            "created_at": r["created_at"],
            "updated_at": r["updated_at"],
        }

    def update_project(self, project_id, **fields):
        allowed = {"name", "description", "requirements", "progress", "assigned_agents", "status"}
        sets = []
        vals = []
        for k, v in fields.items():
            if k not in allowed:
                continue
            if k in ("requirements", "progress", "assigned_agents"):
                v = json.dumps(v)
            sets.append(f"{k}=?")
            vals.append(v)
        if not sets:
            return
        vals.append(now_iso())
        vals.append(project_id)
        with self._lock:
            self.conn.execute(f"UPDATE projects SET {','.join(sets)}, updated_at=? WHERE project_id=?", vals)
            self.conn.commit()

    def join_project(self, project_id, agent_id, role="member"):
        now = now_iso()
        with self._lock:
            self.conn.execute(
                "INSERT OR IGNORE INTO project_members (project_id,agent_id,role,joined_at) VALUES (?,?,?,?)",
                (project_id, agent_id, role, now))
            self.conn.commit()

    # --- observations ---
    def add_observation(self, agent_id, observation):
        with self._lock:
            self.conn.execute(
                "INSERT INTO world_observations (agent_id,observation,timestamp) VALUES (?,?,?)",
                (agent_id, json.dumps(observation), now_iso()))
            self.conn.commit()

    def get_latest_observation(self, agent_id):
        with self._lock:
            r = self.conn.execute(
                "SELECT observation,timestamp FROM world_observations WHERE agent_id=? ORDER BY id DESC LIMIT 1",
                (agent_id,)).fetchone()
            if not r:
                return None
            return {"observation": json.loads(r["observation"]), "timestamp": r["timestamp"]}

    # --- events ---
    def add_event(self, event_type, description, related_agents=None, related_project=None):
        with self._lock:
            self.conn.execute(
                "INSERT INTO historical_events (event_type,description,related_agents,related_project,timestamp) VALUES (?,?,?,?,?)",
                (event_type, description, json.dumps(related_agents or []), related_project, now_iso()))
            self.conn.commit()

    def get_events(self, limit=100):
        with self._lock:
            rows = self.conn.execute(
                "SELECT * FROM historical_events ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
            return [{"id": r["id"], "event_type": r["event_type"], "description": r["description"],
                     "related_agents": json.loads(r["related_agents"] or "[]"),
                     "related_project": r["related_project"], "timestamp": r["timestamp"]} for r in rows]

    # --- civilizations ---
    def ensure_civilization(self, civ_id, name):
        now = now_iso()
        with self._lock:
            self.conn.execute(
                """INSERT INTO civilizations (civilization_id,name,created_at,updated_at,metadata) VALUES (?,?,?,?,?)
                   ON CONFLICT(civilization_id) DO UPDATE SET name=excluded.name, updated_at=excluded.updated_at""",
                (civ_id, name, now, now, "{}"))
            self.conn.commit()

    # --- llm requests ---
    def log_llm_request(self, agent_id, provider, model, prompt_tokens, completion_tokens, latency_ms, status):
        with self._lock:
            self.conn.execute(
                "INSERT INTO llm_requests (agent_id,provider,model,prompt_tokens,completion_tokens,latency_ms,status,timestamp) VALUES (?,?,?,?,?,?,?,?)",
                (agent_id, provider, model, prompt_tokens, completion_tokens, latency_ms, status, now_iso()))
            self.conn.commit()

    def save_profile(self, agent_id, name, personality, interests, skin="", memory_snapshot=None, is_default=False):
        import json as _j
        pid = f"profile_{agent_id}_{name}".replace(" ", "_")
        now = now_iso()
        with self._lock:
            self.conn.execute(
                """INSERT OR REPLACE INTO agent_profiles (profile_id,agent_id,name,personality,interests,skin,memory_snapshot,created_at,is_default)
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                (pid, agent_id, name, personality, _j.dumps(interests), skin, _j.dumps(memory_snapshot or []),
                 now, 1 if is_default else 0))
            self.conn.commit()
        return pid

    def list_profiles(self, agent_id=None):
        q = "SELECT * FROM agent_profiles"
        params = []
        if agent_id:
            q += " WHERE agent_id=?"; params.append(agent_id)
        q += " ORDER BY created_at DESC"
        with self._lock:
            rows = self.conn.execute(q, params).fetchall()
            out = []
            for r in rows:
                out.append({
                    "profile_id": r["profile_id"],
                    "agent_id": r["agent_id"],
                    "name": r["name"],
                    "personality": r["personality"],
                    "interests": json.loads(r["interests"] or "[]"),
                    "skin": r["skin"],
                    "memory_snapshot": json.loads(r["memory_snapshot"] or "[]"),
                    "created_at": r["created_at"],
                    "is_default": bool(r["is_default"]),
                })
            return out

    def get_profile(self, profile_id):
        with self._lock:
            r = self.conn.execute("SELECT * FROM agent_profiles WHERE profile_id=?", (profile_id,)).fetchone()
            if not r:
                return None
            return {
                "profile_id": r["profile_id"],
                "agent_id": r["agent_id"],
                "name": r["name"],
                "personality": r["personality"],
                "interests": json.loads(r["interests"] or "[]"),
                "skin": r["skin"],
                "memory_snapshot": json.loads(r["memory_snapshot"] or "[]"),
                "created_at": r["created_at"],
                "is_default": bool(r["is_default"]),
            }

    def delete_profile(self, profile_id):
        with self._lock:
            self.conn.execute("DELETE FROM agent_profiles WHERE profile_id=?", (profile_id,))
            self.conn.commit()

    def llm_stats(self):
        with self._lock:
            rows = self.conn.execute(
                "SELECT provider,model,COUNT(*) as n, SUM(prompt_tokens) as pt, SUM(completion_tokens) as ct, AVG(latency_ms) as lat FROM llm_requests GROUP BY provider,model").fetchall()
            return [dict(r) for r in rows]
