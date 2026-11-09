"""Mock Minecraft world bridge for offline/demo operation."""
from __future__ import annotations

import random
import time
from typing import Any, Dict, Optional

from app.world.bridge import WorldBridge


class MockWorldBridge(WorldBridge):
    def __init__(self):
        self.agents: Dict[str, Dict[str, Any]] = {}
        self.world_time = 0
        self.blocks = {"oak_log": 18, "stone": 120, "dirt": 200, "water": 2}

    def _ensure(self, agent_id: str):
        if agent_id not in self.agents:
            self.agents[agent_id] = {
                "position": {"x": random.randint(-50, 50), "y": 64, "z": random.randint(-50, 50)},
                "health": 20.0,
                "inventory": {},
                "biome": random.choice(["plains", "forest", "river"]),
            }

    def get_observation(self, agent_id: str) -> Optional[Dict[str, Any]]:
        self._ensure(agent_id)
        a = self.agents[agent_id]
        return {
            "agent_id": agent_id,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "world_id": "mock",
            "position": dict(a["position"]),
            "biome": a["biome"],
            "health": a["health"],
            "inventory": dict(a["inventory"]),
            "nearby_blocks": dict(self.blocks),
            "nearby_entities": ["cow", "sheep"],
            "nearby_agents": [x for x in self.agents if x != agent_id],
        }

    def execute_action(self, agent_id: str, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        self._ensure(agent_id)
        a = self.agents[agent_id]
        # deterministic-ish mock execution
        if action == "move_to":
            x = parameters.get("x", a["position"]["x"])
            y = parameters.get("y", a["position"]["y"])
            z = parameters.get("z", a["position"]["z"])
            a["position"] = {"x": x, "y": y, "z": z}
            return {"success": True, "message": "moved"}
        if action == "mine_block":
            bt = parameters.get("block_type", "stone")
            a["inventory"][bt] = a["inventory"].get(bt, 0) + 1
            if bt in self.blocks:
                self.blocks[bt] = max(0, self.blocks[bt] - 1)
            return {"success": True, "collected": bt}
        if action == "collect_item":
            it = parameters.get("item", "item")
            a["inventory"][it] = a["inventory"].get(it, 0) + 1
            return {"success": True, "collected": it}
        if action == "craft_item":
            item = parameters.get("item", "craft")
            a["inventory"][item] = a["inventory"].get(item, 0) + 1
            return {"success": True, "crafted": item}
        if action == "eat_food":
            a["health"] = min(20.0, a["health"] + 2)
            return {"success": True}
        if action == "scan_area":
            return {"success": True, "blocks": dict(self.blocks)}
        if action in ("send_message", "start_project", "join_project"):
            return {"success": True}
        # default
        return {"success": True, "action": action}

    def health(self) -> Dict[str, Any]:
        return {"status": "ok", "mode": "mock", "agents": len(self.agents)}
