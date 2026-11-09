import os
import tempfile
import unittest
from app.database import Database


class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.fd, self.path = tempfile.mkstemp(suffix=".db")
        os.close(self.fd)
        os.remove(self.path)
        self.db = Database(self.path)

    def tearDown(self):
        self.db.close()
        try:
            os.remove(self.path)
        except FileNotFoundError:
            pass

    def test_upsert_and_get_agent(self):
        self.db.upsert_agent("a1", "CHAIWALA", "curious", ["leadership"], {"current_goal": "explore"})
        row = self.db.get_agent("a1")
        self.assertEqual(row["name"], "CHAIWALA")
        self.assertEqual(row["current_goal"], "explore")

    def test_memories(self):
        self.db.upsert_agent("a1", "CHAIWALA", "curious", [])
        self.db.add_memory({"memory_id": "m1", "agent_id": "a1", "memory_type": "episodic", "content": "hello", "importance": 0.8})
        mems = self.db.get_memories("a1")
        self.assertEqual(len(mems), 1)
        self.assertEqual(mems[0]["content"], "hello")

    def test_messages(self):
        self.db.add_message({"message_id": "msg1", "conversation_id": "c1", "sender": "a1", "receiver": "a2", "content": "hi"})
        msgs = self.db.get_messages(agent_id="a1")
        self.assertEqual(len(msgs), 1)

    def test_actions(self):
        self.db.add_action({"action_id": "act1", "agent_id": "a1", "action": "move_to", "parameters": {"x": 1}, "status": "queued"})
        self.db.update_action("act1", status="succeeded", result={"ok": True})
        a = self.db.get_action("act1")
        self.assertEqual(a["status"], "succeeded")
        self.assertEqual(a["result"]["ok"], True)

    def test_projects(self):
        self.db.add_project({"project_id": "p1", "name": "Hall", "proposed_by": "a1", "requirements": {"stone": 10}, "progress": {}, "assigned_agents": ["a1"], "status": "planning"})
        p = self.db.get_project("p1")
        self.assertEqual(p["name"], "Hall")
        self.db.update_project("p1", status="active", progress={"stone": 5})
        p2 = self.db.get_project("p1")
        self.assertEqual(p2["status"], "active")
        self.assertEqual(p2["progress"]["stone"], 5)

    def test_events_and_civ(self):
        self.db.ensure_civilization("civ1", "TestCiv")
        self.db.add_event("test", "something happened", related_agents=["a1"])
        evs = self.db.get_events()
        self.assertEqual(len(evs), 1)
        self.assertEqual(evs[0]["event_type"], "test")

    def test_relationships(self):
        self.db.upsert_relationship("a1", "a2", trust=0.7, familiarity=0.2, notes="friend")
        r = self.db.get_relationship("a1", "a2")
        self.assertAlmostEqual(r["trust"], 0.7)
        self.assertEqual(r["notes"], "friend")

    def test_restart_recovery(self):
        self.db.upsert_agent("a1", "CHAIWALA", "curious", [])
        self.db.add_memory({"memory_id": "m2", "agent_id": "a1", "memory_type": "long_term", "content": "persisted", "importance": 0.9})
        self.db.close()
        db2 = Database(self.path)
        self.assertEqual(db2.get_agent("a1")["name"], "CHAIWALA")
        self.assertEqual(len(db2.get_memories("a1")), 1)
        db2.close()


if __name__ == "__main__":
    unittest.main()
