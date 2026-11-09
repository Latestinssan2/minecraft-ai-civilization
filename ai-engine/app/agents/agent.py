"""Core Agent representation."""
from __future__ import annotations

import json
import threading
import time
from typing import Any, Dict, List, Optional

from app.config import AgentConfig
from app.database import Database
from app.models import AgentState, Decision, Memory, Message, new_id, now_iso
from app.providers.base import BaseProvider


class Agent:
    def __init__(self, cfg: AgentConfig, db: Database, provider: BaseProvider, civ_instruction: str = ""):
        self.cfg = cfg
        self.agent_id = cfg.agent_id
        self.name = cfg.name
        self.personality = cfg.personality
        self.interests = list(cfg.interests)
        self.db = db
        self.provider = provider
        self.civ_instruction = civ_instruction
        self.state = AgentState(
            agent_id=self.agent_id,
            name=self.name,
            personality=self.personality,
            interests=self.interests,
        )
        self._lock = threading.RLock()
        self.last_observation: Optional[Dict[str, Any]] = None
        self.pending_actions: List[Dict[str, Any]] = []
        self._load_from_db()

    def _load_from_db(self):
        row = self.db.get_agent(self.agent_id)
        if row:
            self.state.current_goal = row.get("current_goal", "") or ""
            self.state.current_activity = row.get("current_activity", "idle") or "idle"
            self.state.position = row.get("position", {}) or {}
            self.state.health = row.get("health", 20.0)
            self.state.inventory = row.get("inventory", {}) or {}
            self.state.last_decision_at = row.get("last_decision_at")
            self.state.last_message = row.get("last_message")
            self.state.status = row.get("status", "active") or "active"
        else:
            self.db.upsert_agent(self.agent_id, self.name, self.personality, self.interests,
                                 self.state.to_dict())

    def persist(self):
        self.db.upsert_agent(self.agent_id, self.name, self.personality, self.interests, self.state.to_dict())

    def set_observation(self, obs: Dict[str, Any]):
        with self._lock:
            self.last_observation = obs
            self.state.position = obs.get("position", self.state.position) or self.state.position
            self.state.health = obs.get("health", self.state.health)
            self.state.hunger = obs.get("hunger", self.state.hunger)
            self.state.inventory = obs.get("inventory", self.state.inventory) or self.state.inventory
            self.state.hotbar_slot = obs.get("hotbar_slot", self.state.hotbar_slot)
            # alert detection
            mobs = obs.get("nearby_mobs", []) or []
            dropped = obs.get("dropped_items", []) or []
            if mobs:
                self.state.alert = f"Mob nearby: {mobs[0].get('type','unknown')}"
            elif dropped:
                self.state.alert = f"Item dropped: {dropped[0].get('item','item')}"
            else:
                self.state.alert = None
            self.db.add_observation(self.agent_id, obs)

    def retrieve_memories(self, limit: int = 12, min_importance: float = 0.3) -> List[Dict[str, Any]]:
        mems = self.db.get_memories(self.agent_id, limit=limit, min_importance=min_importance)
        shared = self.db.get_shared_memories(limit=6)
        # merge, dedup by id
        seen = set()
        out = []
        for m in mems + shared:
            if m["memory_id"] in seen:
                continue
            seen.add(m["memory_id"])
            out.append(m)
        return out

    def build_prompt(self) -> tuple[str, str]:
        system = (
            f"You are {self.name}, an independent member of a Minecraft civilization.\n"
            f"Personality: {self.personality}\n"
            f"Interests: {', '.join(self.interests)}\n"
            "You make your own decisions based on observations, memories, and goals.\n"
            "Respond ONLY with a valid JSON object. Do not include markdown or extra text.\n"
            "JSON schema:\n"
            "{\n"
            '  "current_goal": string,\n'
            '  "intention": string (what you want to do next),\n'
            '  "thoughts": string (concise reasoning summary),\n'
            '  "plan": [string, ...],\n'
            '  "priority": "low"|"medium"|"high",\n'
            '  "actions": [{"action": string, "parameters": object}, ...],\n'
            '  "messages": [{"to": string (agent id or "broadcast"), "content": string}] (optional)\n'
            "}\n"
            "Allowed actions: move_to, look_at, follow_agent, stop_moving, mine_block, collect_item, place_block, "
            "interact_with_block, craft_item, equip_item, drop_item, store_item, eat_food, sleep, send_message, "
            "start_project, join_project, scan_area, locate_structure, auto_walk, place_sign, read_sign, pvp_attack, "
            "switch_hotbar, automine, alert_response.\n"
            "Do not claim to have completed actions; only propose them.\n"
        )
        if self.civ_instruction:
            system += f"\nCivilization instruction:\n{self.civ_instruction}\n"

        # context
        obs = self.last_observation or {}
        mems = self.retrieve_memories(limit=10)
        mem_text = "\n".join(f"- [{m['memory_type']}] {m['content']}" for m in mems) or "(none)"
        rels = self.db.list_relationships(self.agent_id)
        rel_text = "\n".join(f"- {r['agent_a']}->{r['agent_b']}: trust={r['trust']:.2f}" for r in rels) or "(none)"
        projects = self.db.list_projects()
        proj_text = "\n".join(f"- {p['name']} ({p['status']}) by {p['proposed_by']}" for p in projects) or "(none)"
        recent_msgs = self.db.get_messages(agent_id=self.agent_id, limit=8)
        msg_text = "\n".join(f"- {m['sender']}->{m['receiver']}: {m['content']}" for m in reversed(recent_msgs)) or "(none)"

        user = (
            f"Your current goal: {self.state.current_goal or '(none)'}\n"
            f"Current activity: {self.state.current_activity}\n"
            f"Intention: {self.state.intention or '(none)'}\n"
            f"Health: {self.state.health} Hunger: {self.state.hunger}\n"
            f"Hotbar slot: {self.state.hotbar_slot}\n"
            f"Alert: {self.state.alert or 'none'}\n"
            f"Observation: {json.dumps(obs)}\n"
            f"Memories:\n{mem_text}\n"
            f"Relationships:\n{rel_text}\n"
            f"Projects:\n{proj_text}\n"
            f"Recent messages:\n{msg_text}\n"
            "Decide your next goal and actions. Return JSON only."
        )
        return system, user

    def decide(self) -> Optional[Decision]:
        system, user = self.build_prompt()
        t0 = time.time()
        try:
            resp = self.provider.generate(system, user, model=self.cfg.model or None, json_mode=True,
                                         timeout=self.provider.cfg.timeout if hasattr(self.provider, "cfg") else None)
        except Exception as e:
            self.db.log_llm_request(self.agent_id, self.provider.name, self.cfg.model or "", 0, 0, 0, f"error:{e}")
            return None
        latency = int((time.time() - t0) * 1000)
        # parse JSON
        text = resp.text.strip()
        # strip code fences if present
        if text.startswith("```"):
            text = text.strip("`")
            # remove leading language tag
            lines = text.splitlines()
            if lines and lines[0].strip().lower() in ("json",):
                lines = lines[1:]
            text = "\n".join(lines).strip()
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            # try to find JSON object
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1:
                try:
                    data = json.loads(text[start:end+1])
                except Exception:
                    data = {}
            else:
                data = {}
        if not isinstance(data, dict):
            data = {}

        actions_raw = data.get("actions", []) or []
        # normalize actions into Action dicts
        norm_actions = []
        for a in actions_raw:
            if not isinstance(a, dict):
                continue
            norm_actions.append({
                "action": a.get("action", ""),
                "parameters": a.get("parameters", {}) or {},
            })

        dec = Decision(
            decision_id=new_id("dec"),
            agent_id=self.agent_id,
            current_goal=data.get("current_goal", self.state.current_goal or ""),
            reasoning_summary=data.get("reasoning_summary", data.get("thoughts", "")),
            intention=data.get("intention", ""),
            thoughts=data.get("thoughts", data.get("reasoning_summary", "")),
            plan=data.get("plan", []) or [],
            priority=data.get("priority", "medium"),
            actions=norm_actions,
            provider_latency_ms=resp.latency_ms or latency,
        )
        self.db.add_decision(dec.to_dict())
        with self._lock:
            self.state.current_goal = dec.current_goal
            self.state.intention = dec.intention
            self.state.thoughts = dec.thoughts
            self.state.current_activity = "planning"
            self.state.last_decision_at = now_iso()
        self.persist()

        # handle messages proposed
        for m in (data.get("messages") or []):
            if not isinstance(m, dict):
                continue
            to = m.get("to", "broadcast")
            content = m.get("content", "")
            if not content:
                continue
            self.send_message(to, content, context="decision")

        # queue actions
        for a in norm_actions:
            self.queue_action(a["action"], a["parameters"])

        # log llm request
        self.db.log_llm_request(self.agent_id, self.provider.name, resp.model, resp.prompt_tokens,
                                resp.completion_tokens, resp.latency_ms, "ok")
        return dec

    def queue_action(self, action: str, parameters: Dict[str, Any]) -> str:
        from app.models import Action, new_id
        aid = new_id("action")
        act = Action(action_id=aid, agent_id=self.agent_id, action=action, parameters=parameters, status="queued")
        self.db.add_action(act.to_dict())
        self.pending_actions.append(act.to_dict())
        return aid

    def send_message(self, to: str, content: str, context: Optional[str] = None, project_id: Optional[str] = None):
        conv_id = f"conv_{self.agent_id}_{to}"
        # normalize broadcast conversation
        if to == "broadcast":
            conv_id = "conv_broadcast"
        self.db.upsert_conversation(conv_id, [self.agent_id, to] if to != "broadcast" else [self.agent_id], topic=context)
        from app.models import Message, new_id
        msg = Message(message_id=new_id("msg"), conversation_id=conv_id, sender=self.agent_id,
                      receiver=to, content=content, context=context, project_id=project_id)
        self.db.add_message(msg.to_dict())
        with self._lock:
            self.state.last_message = content
        self.persist()
        # update familiarity
        if to not in ("broadcast",) and not to.startswith("group:"):
            self.db.upsert_relationship(self.agent_id, to, familiarity=0.1)
            try:
                self.db.upsert_relationship(to, self.agent_id, familiarity=0.1)
            except Exception:
                pass

    def add_memory(self, content: str, memory_type: str = "episodic", importance: float = 0.5,
                   related_agents: Optional[List[str]] = None, related_project: Optional[str] = None):
        from app.memory.memory_manager import MemoryManager
        mm = MemoryManager(self.db)
        # dedup
        if mm.is_duplicate(self.agent_id, content):
            return
        # score importance
        importance = mm.score_importance(content, base=importance)
        from app.models import Memory, new_id
        mem = Memory(memory_id=new_id("mem"), agent_id=self.agent_id, memory_type=memory_type,
                     importance=importance, content=content, related_agents=related_agents or [],
                     related_project=related_project)
        self.db.add_memory(mem.to_dict())

    def to_state_dict(self) -> Dict[str, Any]:
        return self.state.to_dict()
