import os
import tempfile
import unittest
from app.config import AgentConfig
from app.database import Database
from app.providers.mock_provider import MockProvider
from app.agents.agent import Agent


class TestAgent(unittest.TestCase):
    def setUp(self):
        self.fd, self.path = tempfile.mkstemp(suffix=".db")
        os.close(self.fd)
        os.remove(self.path)
        self.db = Database(self.path)
        self.cfg = AgentConfig(agent_id="agent_01", name="CHAIWALA", personality="curious", interests=["leadership"])
        self.provider = MockProvider()
        self.agent = Agent(self.cfg, self.db, self.provider, "civilization instruction")

    def tearDown(self):
        self.db.close()
        try:
            os.remove(self.path)
        except FileNotFoundError:
            pass

    def test_initial_state(self):
        self.assertEqual(self.agent.name, "CHAIWALA")
        self.assertEqual(self.agent.agent_id, "agent_01")

    def test_set_observation(self):
        obs = {"agent_id": "agent_01", "position": {"x": 1, "y": 2, "z": 3}, "health": 18, "inventory": {"stone": 5}}
        self.agent.set_observation(obs)
        self.assertEqual(self.agent.state.health, 18)
        self.assertEqual(self.agent.state.inventory.get("stone"), 5)

    def test_decide(self):
        self.agent.set_observation({"agent_id": "agent_01", "position": {"x": 0, "y": 64, "z": 0}, "health": 20, "inventory": {}})
        dec = self.agent.decide()
        self.assertIsNotNone(dec)
        self.assertTrue(dec.current_goal)
        # actions queued
        acts = self.db.list_actions(agent_id="agent_01")
        self.assertGreaterEqual(len(acts), 1)

    def test_send_message(self):
        self.agent.send_message("agent_02", "hello there")
        msgs = self.db.get_messages(agent_id="agent_01")
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0]["content"], "hello there")

    def test_add_memory(self):
        self.agent.add_memory("test memory", memory_type="episodic", importance=0.7)
        mems = self.db.get_memories("agent_01")
        self.assertEqual(len(mems), 1)
        self.assertEqual(mems[0]["content"], "test memory")

    def test_persistence(self):
        self.agent.state.current_goal = "build house"
        self.agent.persist()
        row = self.db.get_agent("agent_01")
        self.assertEqual(row["current_goal"], "build house")


if __name__ == "__main__":
    unittest.main()
