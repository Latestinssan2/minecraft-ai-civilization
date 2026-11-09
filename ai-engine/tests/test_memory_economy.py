import os
import tempfile
import unittest
from app.database import Database
from app.memory.memory_manager import MemoryManager
from app.civilization.economy import Economy


class TestMemoryEconomy(unittest.TestCase):
    def setUp(self):
        self.fd, self.path = tempfile.mkstemp(suffix=".db")
        os.close(self.fd)
        os.remove(self.path)
        self.db = Database(self.path)
        self.mm = MemoryManager(self.db)
        self.eco = Economy(self.db)

    def tearDown(self):
        self.db.close()
        try:
            os.remove(self.path)
        except FileNotFoundError:
            pass

    def test_dedup(self):
        self.db.upsert_agent("a1", "A", "p", [])
        self.mm.add_if_novel("a1", "hello world", importance=0.5)
        self.assertFalse(self.mm.add_if_novel("a1", "hello world", importance=0.5))
        self.assertEqual(len(self.db.get_memories("a1")), 1)

    def test_score_importance(self):
        s = self.mm.score_importance("Agent helped build the first house")
        self.assertGreater(s, 0.5)

    def test_summarize_archives(self):
        self.db.upsert_agent("a1", "A", "p", [])
        for i in range(5):
            self.db.add_memory({"memory_id": f"m{i}", "agent_id": "a1", "memory_type": "episodic",
                                "content": f"low {i}", "importance": 0.2})
        self.mm.summarize("a1", keep=2)
        mems = self.db.get_memories("a1")
        self.assertLessEqual(len(mems), 2)

    def test_economy_transfer(self):
        self.eco.record("stone", 10, "a1", "mined")
        self.eco.transfer("stone", 4, "a1", "a2", "trade")
        self.assertEqual(self.eco.balance("a1", "stone"), 6)
        self.assertEqual(self.eco.balance("a2", "stone"), 4)

    def test_retrieve_relevant(self):
        self.db.upsert_agent("a1", "A", "p", [])
        self.db.add_memory({"memory_id": "m1", "agent_id": "a1", "memory_type": "episodic", "content": "found river", "importance": 0.6})
        self.db.add_memory({"memory_id": "m2", "agent_id": "a1", "memory_type": "episodic", "content": "built house", "importance": 0.6})
        res = self.mm.retrieve_relevant("a1", "river location")
        self.assertTrue(any("river" in m["content"] for m in res))


if __name__ == "__main__":
    unittest.main()
