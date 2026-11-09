"""Entry point for the AI engine."""
from __future__ import annotations

import argparse
import json
import os
import threading
import time

from app.agents.agent import Agent
from app.agents.scheduler import AgentScheduler
from app.api.server import AppContext, create_server
from app.api.websocket import WebSocketHub
from app.civilization.projects import ProjectManager
from app.communication.message_bus import MessageBus
from app.config import load_config
from app.database import Database
from app.models import new_id, now_iso
from app.providers.ollama_provider import OllamaProvider
from app.providers.mock_provider import MockProvider
from app.world.mock_world import MockWorldBridge


def build_app(config_path: str):
    cfg = load_config(config_path)
    db = Database(cfg.database_path)
    db.ensure_civilization("civ_01", cfg.civilization_name)

    # provider
    ollama_cfg = cfg.ollama
    provider = OllamaProvider(ollama_cfg)

    bridge = MockWorldBridge()

    # load civilization instruction
    civ_instruction = cfg.initial_instruction or ""
    if not civ_instruction:
        # default from docs
        civ_instruction = (
            "You are an independent member of a new civilization in Minecraft. "
            "Your civilization begins with no established society. "
            "Your objective is to survive, cooperate, explore, develop resources, establish settlements, "
            "construct buildings, and create a functioning society. "
            "Make decisions using actual observations of the Minecraft world. "
            "Do not claim to have collected resources, built structures, or completed actions unless they actually happened."
        )

    agents = []
    agent_configs = cfg.agents
    if not agent_configs:
        from app.agents.personality import DEFAULT_PERSONALITIES
        for aid, info in DEFAULT_PERSONALITIES.items():
            from app.config import AgentConfig
            agent_configs.append(AgentConfig(agent_id=aid, name=info["name"], personality=info["personality"],
                                            interests=info["interests"]))
    for ac in agent_configs:
        if not ac.personality:
            from app.agents.personality import DEFAULT_PERSONALITIES
            info = DEFAULT_PERSONALITIES.get(ac.agent_id, {})
            ac.personality = info.get("personality", ac.personality)
            if not ac.interests:
                ac.interests = info.get("interests", [])
        # persist identity
        db.upsert_agent(ac.agent_id, ac.name, ac.personality, ac.interests, {})
        agents.append(Agent(ac, db, provider, civ_instruction))

    # seed initial memories
    for a in agents:
        existing = db.get_memories(a.agent_id, limit=1)
        if not existing:
            a.add_memory(f"I am {a.name}, founding member of {cfg.civilization_name}.", memory_type="long_term", importance=0.9)
            # relationships with others
            for other in agents:
                if other.agent_id != a.agent_id:
                    db.upsert_relationship(a.agent_id, other.agent_id, trust=0.5, familiarity=0.1,
                                           notes=f"Initial fellow citizen")

    message_bus = MessageBus(db)
    project_manager = ProjectManager(db)

    ws_hub = WebSocketHub(host=cfg.host, port=cfg.port + 1)

    scheduler = AgentScheduler(agents, interval_seconds=cfg.decision_interval_seconds,
                               concurrency=cfg.max_concurrent_ai)

    ctx = AppContext(cfg, db, bridge, agents, scheduler, message_bus, project_manager, ws_hub)

    # observation sync thread: pull from bridge into agents periodically (mock mode only)
    if cfg.use_mock_world:
        def obs_loop():
            while True:
                for a in agents:
                    try:
                        obs = bridge.get_observation(a.agent_id)
                        if obs:
                            a.set_observation(obs)
                    except Exception:
                        pass
                time.sleep(5)
        threading.Thread(target=obs_loop, daemon=True).start()

        from app.actions.executor import ActionExecutor
        executor = ActionExecutor(db, bridge, poll_interval=1.0)
        executor.start()
    else:
        executor = None

    # broadcaster
    def broadcast_loop():
        while True:
            ctx.broadcast_state()
            time.sleep(5)
    threading.Thread(target=broadcast_loop, daemon=True).start()

    return cfg, ctx, scheduler, ws_hub, db


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/civilization.yaml")
    parser.add_argument("--host", default=None)
    parser.add_argument("--port", type=int, default=None)
    args = parser.parse_args()

    cfg, ctx, scheduler, ws_hub, db = build_app(args.config)
    host = args.host or cfg.host
    port = args.port or cfg.port

    ws_hub.start()
    scheduler.start()

    httpd = create_server(ctx, host, port)
    print(f"AI engine running on http://{host}:{port}")
    print(f"WebSocket on ws://{host}:{port+1}")
    print(f"Ollama: {cfg.ollama.base_url} model={cfg.ollama.model}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        scheduler.stop()
        ws_hub.stop()
        db.close()


if __name__ == "__main__":
    main()
