import os
import tempfile
import threading
import time
import unittest
import urllib.request
import json

from app.config import load_config
from app.main import build_app
from app.api.server import create_server


class TestAPI(unittest.TestCase):
    def setUp(self):
        self.fd, self.dbpath = tempfile.mkstemp(suffix=".db")
        os.close(self.fd)
        os.remove(self.dbpath)
        # write a temp config
        self.cfgpath = tempfile.mktemp(suffix=".yaml")
        with open(self.cfgpath, "w") as f:
            f.write(f"database_path: {self.dbpath}\nport: 8099\nhost: 127.0.0.1\ndecision_interval_seconds: 999\n")
        self.cfg, self.ctx, self.sched, self.ws, self.db = build_app(self.cfgpath)
        self.httpd = create_server(self.ctx, "127.0.0.1", 8099)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        time.sleep(1)

    def tearDown(self):
        self.httpd.shutdown()
        self.sched.stop()
        self.ws.stop()
        self.db.close()
        for p in (self.cfgpath, self.dbpath):
            try:
                os.remove(p)
            except FileNotFoundError:
                pass

    def _get(self, path):
        with urllib.request.urlopen("http://127.0.0.1:8099" + path) as r:
            return json.loads(r.read())

    def _post(self, path, body):
        data = json.dumps(body).encode()
        req = urllib.request.Request("http://127.0.0.1:8099" + path, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())

    def test_health(self):
        d = self._get("/api/health")
        self.assertEqual(d["status"], "ok")

    def test_agents(self):
        d = self._get("/api/agents")
        self.assertEqual(len(d), 3)
        names = [a["name"] for a in d]
        self.assertIn("CHAIWALA", names)

    def test_civilization(self):
        d = self._get("/api/civilization")
        self.assertEqual(d["agent_count"], 3)

    def test_create_project(self):
        p = self._post("/api/projects", {"name": "Hall", "proposed_by": "agent_01", "requirements": {"stone": 5}})
        self.assertEqual(p["name"], "Hall")
        d = self._get("/api/projects")
        self.assertEqual(len(d), 1)

    def test_send_message(self):
        m = self._post("/api/messages", {"sender": "agent_01", "receiver": "agent_02", "content": "hello"})
        self.assertEqual(m["content"], "hello")
        msgs = self._get("/api/messages?agent_id=agent_02")
        self.assertEqual(len(msgs), 1)

    def test_ollama_health(self):
        d = self._get("/api/ollama/health")
        self.assertIn("status", d)

    def test_observe_and_pending(self):
        self._post("/api/observations", {"agent_id": "agent_01", "observation": {"position": {"x": 1, "y": 2, "z": 3}, "health": 20, "inventory": {}}})
        o = self._get("/api/agents/agent_01/observations")
        self.assertIn("position", o["observation"])
        # queue an action via decide (mock provider) won't run because no scheduler; but queue manually not needed
        # pending endpoint
        pending = self._get("/api/agents/agent_01/actions/pending")
        self.assertIsInstance(pending, list)


if __name__ == "__main__":
    unittest.main()
