import os
import tempfile
import time
import unittest
from app.config import load_config, AppConfig, AgentConfig
from app.database import Database
from app.providers.mock_provider import MockProvider
from app.agents.agent import Agent
from app.communication.message_bus import MessageBus
from app.civilization.projects import ProjectManager


class TestIntegration(unittest.TestCase):
    def setUp(self):
        self.fd, self.path = tempfile.mkstemp(suffix=".db")
        os.close(self.fd)
        os.remove(self.path)
        self.db = Database(self.path)
        self.db.ensure_civilization("civ1", "TestCiv")
        cfgs = [
            AgentConfig(agent_id="agent_01", name="CHAIWALA", personality="curious", interests=["leadership"]),
            AgentConfig(agent_id="agent_02", name="Arin", personality="practical", interests=["construction"]),
            AgentConfig(agent_id="agent_03", name="Mira", personality="adventurous", interests=["exploration"]),
        ]
        provider = MockProvider()
        self.agents = [Agent(c, self.db, provider, "civ instr") for c in cfgs]
        for a in self.agents:
            self.db.upsert_agent(a.agent_id, a.name, a.personality, a.interests, {})
        self.mb = MessageBus(self.db)
        self.pm = ProjectManager(self.db)

    def tearDown(self):
        self.db.close()
        try:
            os.remove(self.path)
        except FileNotFoundError:
            pass

    def test_three_agents_independent(self):
        self.assertEqual(len(self.agents), 3)
        ids = [a.agent_id for a in self.agents]
        self.assertEqual(len(set(ids)), 3)

    def test_communication(self):
        self.agents[0].send_message("agent_02", "We should build a settlement.")
        msgs = self.db.get_messages(agent_id="agent_02")
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0]["content"], "We should build a settlement.")

    def test_project_flow(self):
        proj = self.pm.create("Town Hall", proposed_by="agent_01", requirements={"stone": 5}, assigned_agents=["agent_01", "agent_02"])
        self.assertEqual(proj["status"], "planning")
        self.pm.join(proj["project_id"], "agent_03")
        p = self.db.get_project(proj["project_id"])
        self.assertIn("agent_03", p["assigned_agents"])
        self.pm.update_progress(proj["project_id"], {"stone": 5})
        p2 = self.db.get_project(proj["project_id"])
        self.assertEqual(p2["status"], "completed")

    def test_decision_and_action(self):
        self.agents[0].set_observation({"agent_id": "agent_01", "position": {"x": 0, "y": 64, "z": 0}, "health": 20, "inventory": {}})
        dec = self.agents[0].decide()
        self.assertIsNotNone(dec)
        # run action executor manually
        from app.world.mock_world import MockWorldBridge
        from app.actions.executor import ActionExecutor
        bridge = MockWorldBridge()
        bridge.get_observation("agent_01")
        exe = ActionExecutor(self.db, bridge, poll_interval=0.1)
        # execute queued
        queued = self.db.list_actions(status="queued")
        for a in queued:
            exe._execute_one(a)
        done = self.db.list_actions(status="succeeded")
        self.assertGreaterEqual(len(done), 1)

    def test_memory_persistence(self):
        self.agents[1].add_memory("Arin helped build", memory_type="episodic", importance=0.9, related_agents=["agent_01"])
        mems = self.db.get_memories("agent_02")
        self.assertEqual(len(mems), 1)
        self.assertEqual(mems[0]["related_agents"], ["agent_01"])

    def test_relationships_tracked(self):
        self.agents[0].send_message("agent_02", "hi")
        r = self.db.get_relationship("agent_01", "agent_02")
        self.assertIsNotNone(r)

    def test_restart_recovery(self):
        self.agents[0].add_memory("persist me", memory_type="long_term", importance=0.8)
        self.db.close()
        db2 = Database(self.path)
        mems = db2.get_memories("agent_01")
        self.assertTrue(any(m["content"] == "persist me" for m in mems))
        db2.close()
        self.db = Database(self.path)


if __name__ == "__main__":
    unittest.main()
