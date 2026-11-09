"""HTTP API server (stdlib)."""
from __future__ import annotations

import json
import threading
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Optional

from app.agents.scheduler import AgentScheduler
from app.civilization.projects import ProjectManager
from app.communication.message_bus import MessageBus
from app.config import AppConfig
from app.database import Database
from app.models import new_id, now_iso
from app.world.bridge import WorldBridge


class AppContext:
    def __init__(self, cfg: AppConfig, db: Database, bridge: WorldBridge, agents, scheduler,
                 message_bus, project_manager, ws_hub):
        self.cfg = cfg
        self.db = db
        self.bridge = bridge
        self.agents = {a.agent_id: a for a in agents}
        self.agent_list = agents
        self.scheduler = scheduler
        self.message_bus = message_bus
        self.project_manager = project_manager
        self.ws_hub = ws_hub
        self.provider = agents[0].provider if agents else None

    def broadcast_state(self):
        try:
            payload = {
                "type": "snapshot",
                "timestamp": now_iso(),
                "agents": [a.to_state_dict() for a in self.agent_list],
                "projects": self.db.list_projects(),
                "events": self.db.get_events(limit=20),
            }
            self.ws_hub.broadcast(json.dumps(payload))
        except Exception:
            pass


def make_handler(ctx: AppContext):
    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def _send_json(self, status: int, data: Any):
            body = json.dumps(data, default=str).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET,POST,PUT,DELETE,OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.end_headers()
            self.wfile.write(body)

        def _read_body(self) -> Dict[str, Any]:
            n = int(self.headers.get("Content-Length", 0))
            if n <= 0:
                return {}
            raw = self.rfile.read(n)
            try:
                return json.loads(raw.decode("utf-8"))
            except Exception:
                return {}

        def do_OPTIONS(self):
            self._send_json(204, {})

        def do_GET(self):
            parsed = urllib.parse.urlparse(self.path)
            path = parsed.path.rstrip("/")
            qs = urllib.parse.parse_qs(parsed.query)
            try:
                self._route_get(path, qs)
            except Exception as e:
                self._send_json(500, {"error": str(e)})

        def do_POST(self):
            parsed = urllib.parse.urlparse(self.path)
            path = parsed.path.rstrip("/")
            body = self._read_body()
            try:
                self._route_post(path, body)
            except Exception as e:
                self._send_json(500, {"error": str(e)})

        def _route_get(self, path, qs):
            if path == "/api/health":
                return self._send_json(200, {"status": "ok", "time": now_iso()})
            if path == "/api/ollama/health":
                return self._send_json(200, ctx.provider.health_check() if hasattr(ctx.provider, "health_check") else ctx.agents[list(ctx.agents)[0]].provider.health_check())
            if path == "/api/ollama/models":
                prov = ctx.agent_list[0].provider
                return self._send_json(200, {"models": prov.list_models()})
            if path == "/api/agents":
                return self._send_json(200, [a.to_state_dict() for a in ctx.agent_list])
            # /api/agents/{id}
            parts = path.split("/")
            if len(parts) >= 4 and parts[1] == "api" and parts[2] == "agents":
                aid = parts[3]
                agent = ctx.agents.get(aid)
                if agent is None:
                    return self._send_json(404, {"error": "agent not found"})
                if len(parts) == 4:
                    return self._send_json(200, agent.to_state_dict())
                sub = parts[4]
                if sub == "memories":
                    limit = int(qs.get("limit", ["50"])[0])
                    return self._send_json(200, ctx.db.get_memories(aid, limit=limit))
                if sub == "decisions":
                    limit = int(qs.get("limit", ["50"])[0])
                    return self._send_json(200, ctx.db.get_decisions(agent_id=aid, limit=limit))
                if sub == "actions":
                    if len(parts) >= 6 and parts[5] == "pending":
                        pending = ctx.db.list_actions(agent_id=aid, status="queued", limit=50)
                        return self._send_json(200, pending)
                    limit = int(qs.get("limit", ["50"])[0])
                    return self._send_json(200, ctx.db.list_actions(agent_id=aid, limit=limit))
                if sub == "observations":
                    o = ctx.db.get_latest_observation(aid)
                    return self._send_json(200, o or {})
                if sub == "actions" and len(parts) >= 6 and parts[5] == "pending":
                    pending = ctx.db.list_actions(agent_id=aid, status="queued", limit=50)
                    return self._send_json(200, pending)
                return self._send_json(404, {"error": "not found"})
            if path == "/api/messages":
                aid = qs.get("agent_id", [None])[0]
                conv = qs.get("conversation_id", [None])[0]
                limit = int(qs.get("limit", ["100"])[0])
                msgs = ctx.db.get_messages(agent_id=aid, conversation_id=conv, limit=limit)
                return self._send_json(200, list(reversed(msgs)))
            if path == "/api/conversations":
                return self._send_json(200, ctx.message_bus.conversations())
            if path == "/api/projects":
                status = qs.get("status", [None])[0]
                return self._send_json(200, ctx.db.list_projects(status=status))
            if path.startswith("/api/projects/"):
                pid = path.split("/")[-1]
                p = ctx.db.get_project(pid)
                if not p:
                    return self._send_json(404, {"error": "project not found"})
                return self._send_json(200, p)
            if path == "/api/events":
                limit = int(qs.get("limit", ["100"])[0])
                return self._send_json(200, ctx.db.get_events(limit=limit))
            if path == "/api/civilization":
                agents = ctx.db.list_agents()
                projects = ctx.db.list_projects()
                events = ctx.db.get_events(limit=10)
                return self._send_json(200, {
                    "name": ctx.cfg.civilization_name,
                    "agent_count": len(agents),
                    "project_count": len(projects),
                    "active_projects": len([p for p in projects if p["status"] == "active"]),
                    "completed_projects": len([p for p in projects if p["status"] == "completed"]),
                    "recent_events": events,
                })
            if path == "/api/relationships":
                aid = qs.get("agent_id", [None])[0]
                return self._send_json(200, ctx.db.list_relationships(agent_id=aid))
            if path == "/api/llm/stats":
                return self._send_json(200, ctx.db.llm_stats())
            if path == "/api/world/positions":
                obs_map = {}
                for a in ctx.agent_list:
                    o = ctx.db.get_latest_observation(a.agent_id)
                    obs_map[a.agent_id] = o["observation"] if o else {}
                return self._send_json(200, obs_map)
            return self._send_json(404, {"error": "not found"})

        def _route_post(self, path, body):
            if path == "/api/observations":
                aid = body.get("agent_id")
                if not aid or aid not in ctx.agents:
                    return self._send_json(400, {"error": "unknown agent"})
                obs = body.get("observation", body)
                ctx.agents[aid].set_observation(obs)
                ctx.db.add_observation(aid, obs)
                # event-driven: trigger decision on alert
                alert = ctx.agents[aid].state.alert
                if alert:
                    ctx.scheduler.trigger(aid, alert)
                    ctx.db.add_event("alert", f"{aid}: {alert}", related_agents=[aid])
                return self._send_json(200, {"status": "ok"})
            if path == "/api/actions/result" or path.startswith("/api/actions/") and path.endswith("/result"):
                aid_action = path.split("/")[3] if len(path.split("/")) > 3 else body.get("action_id")
                action_id = body.get("action_id", aid_action)
                status = body.get("status", "succeeded")
                ctx.db.update_action(action_id, status=status, result=body.get("result"), error=body.get("error"),
                                     completed_at=now_iso())
                ctx.db.add_action_result(action_id, status, result=body.get("result"), error=body.get("error"))
                # memory
                a = ctx.db.get_action(action_id)
                if a:
                    agent = ctx.agents.get(a["agent_id"])
                    if agent:
                        agent.add_memory(f"Action {a['action']} {status}: {body.get('result')}", memory_type="episodic",
                                         importance=0.4)
                return self._send_json(200, {"status": "ok"})
            if path.endswith("/actions/pending") if False else False:
                pass
            # /api/agents/{id}/actions/pending is GET actually; handle POST not needed
            if path == "/api/agents/register":
                # body: agent_id,name,personality,interests
                aid = body.get("agent_id")
                if not aid:
                    return self._send_json(400, {"error": "agent_id required"})
                ctx.cfg  # noop
                return self._send_json(200, {"status": "ok"})
            if path == "/api/agents/decide-all":
                ctx.scheduler.run_once()
                return self._send_json(200, {"status": "queued"})
            if path.startswith("/api/agents/") and path.endswith("/decide"):
                aid = path.split("/")[3]
                agent = ctx.agents.get(aid)
                if not agent:
                    return self._send_json(404, {"error": "agent not found"})
                dec = agent.decide()
                return self._send_json(200, dec.to_dict() if dec else {"status": "no-decision"})
            if path.startswith("/api/agents/") and path.endswith("/model"):
                aid = path.split("/")[3]
                agent = ctx.agents.get(aid)
                if not agent:
                    return self._send_json(404, {"error": "agent not found"})
                model = body.get("model")
                if model:
                    agent.cfg.model = model
                return self._send_json(200, {"status": "ok", "model": agent.cfg.model})
            if path == "/api/messages":
                msg = ctx.message_bus.send(
                    sender=body.get("sender"),
                    receiver=body.get("receiver", "broadcast"),
                    content=body.get("content", ""),
                    context=body.get("context"),
                    project_id=body.get("project_id"),
                )
                # update agent last_message
                s = ctx.agents.get(body.get("sender"))
                if s:
                    s.state.last_message = body.get("content")
                    s.persist()
                ctx.broadcast_state()
                return self._send_json(200, msg)
            if path == "/api/projects":
                proj = ctx.project_manager.create(
                    name=body.get("name", "Unnamed"),
                    proposed_by=body.get("proposed_by", "agent_01"),
                    description=body.get("description", ""),
                    requirements=body.get("requirements", {}),
                    assigned_agents=body.get("assigned_agents", []),
                )
                ctx.broadcast_state()
                return self._send_json(201, proj)
            if path.startswith("/api/projects/") and path.endswith("/join"):
                pid = path.split("/")[3]
                ctx.project_manager.join(pid, body.get("agent_id"), body.get("role", "member"))
                ctx.broadcast_state()
                return self._send_json(200, {"status": "ok"})
            if path.startswith("/api/projects/") and path.endswith("/progress"):
                pid = path.split("/")[3]
                ctx.project_manager.update_progress(pid, body.get("progress", {}))
                ctx.broadcast_state()
                return self._send_json(200, {"status": "ok"})
            if path.startswith("/api/projects/") and path.endswith("/status"):
                pid = path.split("/")[3]
                ctx.project_manager.set_status(pid, body.get("status", "active"))
                ctx.broadcast_state()
                return self._send_json(200, {"status": "ok"})
            if path == "/api/memory":
                aid = body.get("agent_id")
                agent = ctx.agents.get(aid)
                if not agent:
                    return self._send_json(404, {"error": "agent not found"})
                agent.add_memory(body.get("content", ""), memory_type=body.get("memory_type", "episodic"),
                                 importance=body.get("importance", 0.5),
                                 related_agents=body.get("related_agents"),
                                 related_project=body.get("related_project"))
                return self._send_json(200, {"status": "ok"})
            if path == "/api/events":
                ctx.db.add_event(body.get("event_type", "info"), body.get("description", ""),
                                 related_agents=body.get("related_agents"), related_project=body.get("related_project"))
                ctx.broadcast_state()
                return self._send_json(200, {"status": "ok"})
            # pending actions GET handled in GET; but mod may POST? support GET only
            return self._send_json(404, {"error": "not found"})

        def log_message(self, *args):
            pass

    return Handler


def create_server(ctx: AppContext, host: str, port: int) -> ThreadingHTTPServer:
    httpd = ThreadingHTTPServer((host, port), make_handler(ctx))
    return httpd
