"""Shared dataclasses used across the AI engine."""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def new_id(prefix: str = "id") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


@dataclass
class Observation:
    agent_id: str
    timestamp: str = field(default_factory=now_iso)
    world_id: str = "default"
    position: Dict[str, float] = field(default_factory=dict)
    biome: str = "unknown"
    health: float = 20.0
    hunger: float = 20.0
    inventory: Dict[str, int] = field(default_factory=dict)
    hotbar_slot: int = 0
    nearby_mobs: List[Dict[str, Any]] = field(default_factory=list)
    dropped_items: List[Dict[str, Any]] = field(default_factory=list)
    nearby_signs: List[Dict[str, Any]] = field(default_factory=list)
    structures: List[Dict[str, Any]] = field(default_factory=list)
    nearby_blocks: Dict[str, int] = field(default_factory=dict)
    nearby_entities: List[str] = field(default_factory=list)
    nearby_agents: List[str] = field(default_factory=list)
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "timestamp": self.timestamp,
            "world_id": self.world_id,
            "position": self.position,
            "biome": self.biome,
            "health": self.health,
            "hunger": self.hunger,
            "inventory": self.inventory,
            "hotbar_slot": self.hotbar_slot,
            "nearby_blocks": self.nearby_blocks,
            "nearby_entities": self.nearby_entities,
            "nearby_agents": self.nearby_agents,
            "nearby_mobs": self.nearby_mobs,
            "dropped_items": self.dropped_items,
            "nearby_signs": self.nearby_signs,
            "structures": self.structures,
            "extra": self.extra,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Observation":
        return cls(
            agent_id=d.get("agent_id", ""),
            timestamp=d.get("timestamp", now_iso()),
            world_id=d.get("world_id", "default"),
            position=d.get("position", {}) or {},
            biome=d.get("biome", "unknown"),
            health=d.get("health", 20.0),
            hunger=d.get("hunger", 20.0),
            inventory=d.get("inventory", {}) or {},
            hotbar_slot=d.get("hotbar_slot", 0),
            nearby_blocks=d.get("nearby_blocks", {}) or {},
            nearby_entities=d.get("nearby_entities", []) or [],
            nearby_agents=d.get("nearby_agents", []) or [],
            nearby_mobs=d.get("nearby_mobs", []) or [],
            dropped_items=d.get("dropped_items", []) or [],
            nearby_signs=d.get("nearby_signs", []) or [],
            structures=d.get("structures", []) or [],
            extra=d.get("extra", {}) or {},
        )


@dataclass
class Action:
    action_id: str
    agent_id: str
    action: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    status: str = "queued"  # queued, running, succeeded, failed, cancelled
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: str = field(default_factory=now_iso)
    completed_at: Optional[str] = None
    retries: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_id": self.action_id,
            "agent_id": self.agent_id,
            "action": self.action,
            "parameters": self.parameters,
            "status": self.status,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "retries": self.retries,
        }


@dataclass
class Memory:
    memory_id: str
    agent_id: str
    memory_type: str  # short_term, long_term, episodic, social, shared
    importance: float = 0.5
    content: str = ""
    related_agents: List[str] = field(default_factory=list)
    related_project: Optional[str] = None
    timestamp: str = field(default_factory=now_iso)
    summary: Optional[str] = None
    archived: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "memory_id": self.memory_id,
            "agent_id": self.agent_id,
            "memory_type": self.memory_type,
            "importance": self.importance,
            "content": self.content,
            "related_agents": self.related_agents,
            "related_project": self.related_project,
            "timestamp": self.timestamp,
            "summary": self.summary,
            "archived": self.archived,
        }


@dataclass
class Message:
    message_id: str
    conversation_id: str
    sender: str
    receiver: str  # agent id or "broadcast" or "group:<id>"
    content: str
    context: Optional[str] = None
    project_id: Optional[str] = None
    timestamp: str = field(default_factory=now_iso)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "message_id": self.message_id,
            "conversation_id": self.conversation_id,
            "sender": self.sender,
            "receiver": self.receiver,
            "content": self.content,
            "context": self.context,
            "project_id": self.project_id,
            "timestamp": self.timestamp,
        }


@dataclass
class Decision:
    decision_id: str
    agent_id: str
    current_goal: str
    reasoning_summary: str
    intention: str = ""
    thoughts: str = ""
    plan: List[str] = field(default_factory=list)
    priority: str = "medium"
    actions: List[Dict[str, Any]] = field(default_factory=list)
    timestamp: str = field(default_factory=now_iso)
    provider_latency_ms: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "agent_id": self.agent_id,
            "current_goal": self.current_goal,
            "reasoning_summary": self.reasoning_summary,
            "intention": self.intention,
            "thoughts": self.thoughts,
            "plan": self.plan,
            "priority": self.priority,
            "actions": self.actions,
            "timestamp": self.timestamp,
            "provider_latency_ms": self.provider_latency_ms,
        }


@dataclass
class Relationship:
    agent_a: str
    agent_b: str
    trust: float = 0.5
    familiarity: float = 0.0
    notes: str = ""
    updated_at: str = field(default_factory=now_iso)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_a": self.agent_a,
            "agent_b": self.agent_b,
            "trust": self.trust,
            "familiarity": self.familiarity,
            "notes": self.notes,
            "updated_at": self.updated_at,
        }


@dataclass
class Project:
    project_id: str
    name: str
    proposed_by: str
    description: str = ""
    requirements: Dict[str, int] = field(default_factory=dict)
    progress: Dict[str, int] = field(default_factory=dict)
    assigned_agents: List[str] = field(default_factory=list)
    status: str = "planning"  # planning, active, completed, cancelled
    created_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_id": self.project_id,
            "name": self.name,
            "proposed_by": self.proposed_by,
            "description": self.description,
            "requirements": self.requirements,
            "progress": self.progress,
            "assigned_agents": self.assigned_agents,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class AgentState:
    agent_id: str
    name: str
    personality: str
    interests: List[str] = field(default_factory=list)
    current_goal: str = ""
    current_activity: str = "idle"
    intention: str = ""
    thoughts: str = ""
    position: Dict[str, float] = field(default_factory=dict)
    health: float = 20.0
    hunger: float = 20.0
    inventory: Dict[str, int] = field(default_factory=dict)
    hotbar_slot: int = 0
    skin: str = ""
    alert: Optional[str] = None
    last_decision_at: Optional[str] = None
    last_message: Optional[str] = None
    status: str = "active"  # active, paused, error

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "personality": self.personality,
            "interests": self.interests,
            "current_goal": self.current_goal,
            "current_activity": self.current_activity,
            "intention": self.intention,
            "thoughts": self.thoughts,
            "position": self.position,
            "health": self.health,
            "hunger": self.hunger,
            "inventory": self.inventory,
            "hotbar_slot": self.hotbar_slot,
            "skin": self.skin,
            "alert": self.alert,
            "last_decision_at": self.last_decision_at,
            "last_message": self.last_message,
            "status": self.status,
        }
