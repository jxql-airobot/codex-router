import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from memory.decision_memory import DecisionRecord
from memory.experience_memory import ExperienceRecord
from memory.failure_memory import FailureRecord
from memory.project_memory import ProjectMemory
from memory.project_memory_store import ProjectMemoryStore


class DataclassTests(unittest.TestCase):
    def test_decision(self):
        self.assertEqual(DecisionRecord("t", "c", "r").choice, "c")

    def test_failure(self):
        self.assertEqual(FailureRecord("t", "e", "f").fix, "f")

    def test_experience(self):
        self.assertEqual(ExperienceRecord("c", "l").lesson, "l")

    def test_project_memory(self):
        memory = ProjectMemory("p")
        self.assertEqual(memory.project, "p")


class ProjectMemoryStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = ProjectMemoryStore(Path(self.tmp.name) / "memory.json")

    def tearDown(self):
        self.tmp.cleanup()

    def test_add_decision(self):
        self.store.add_decision("p", "通信", "Socket", "兼容ABB")
        self.assertEqual(self.store.decisions("p")[0]["choice"], "Socket")

    def test_add_failure(self):
        self.store.add_failure("p", "ROS2通信", "QoS错误", "修改QoS")
        self.assertEqual(self.store.failures("p")[0]["fix"], "修改QoS")

    def test_add_experience(self):
        self.store.add_experience("p", "launch", "修改后重新build")
        self.assertEqual(self.store.experience("p")[0]["lesson"], "修改后重新build")

    def test_decisions_filter_project(self):
        self.store.add_decision("a", "t", "c", "r")
        self.store.add_decision("b", "t", "c", "r")
        self.assertEqual(len(self.store.decisions("a")), 1)

    def test_failures_filter_project(self):
        self.store.add_failure("a", "t", "e")
        self.store.add_failure("b", "t", "e")
        self.assertEqual(len(self.store.failures("a")), 1)

    def test_experience_filter_project(self):
        self.store.add_experience("a", "c", "l")
        self.store.add_experience("b", "c", "l")
        self.assertEqual(len(self.store.experience("a")), 1)

    def test_query_finds_relevant(self):
        self.store.add_decision("p", "Socket通信", "Socket", "兼容ABB")
        results = self.store.query("p", "Socket")
        self.assertTrue(results)

    def test_query_no_match(self):
        self.store.add_decision("p", "Socket", "Socket", "r")
        self.assertEqual(self.store.query("p", "HTTP"), [])

    def test_persistence(self):
        self.store.add_decision("p", "t", "c", "r")
        second = ProjectMemoryStore(self.store.path)
        self.assertEqual(len(second.decisions("p")), 1)

    def test_empty_store(self):
        self.assertEqual(self.store.decisions(), [])
        self.assertEqual(self.store.failures(), [])
        self.assertEqual(self.store.experience(), [])

    def test_all_decisions(self):
        self.store.add_decision("a", "t", "c", "r")
        self.store.add_decision("b", "t", "c", "r")
        self.assertEqual(len(self.store.decisions()), 2)

    def test_query_decision_type(self):
        self.store.add_decision("p", "topic", "choice", "reason")
        self.assertEqual(self.store.query("p", "topic")[0]["choice"], "choice")

    def test_add_decision_returns_record(self):
        record = self.store.add_decision("p", "t", "c", "r")
        self.assertEqual(record["project"], "p")

    def test_add_failure_returns_record(self):
        record = self.store.add_failure("p", "t", "e")
        self.assertEqual(record["error"], "e")

    def test_add_experience_returns_record(self):
        record = self.store.add_experience("p", "c", "l")
        self.assertEqual(record["context"], "c")

    def test_decision_reason(self):
        self.store.add_decision("p", "t", "c", "reason")
        self.assertEqual(self.store.decisions("p")[0]["reason"], "reason")

    def test_failure_task(self):
        self.store.add_failure("p", "task", "error")
        self.assertEqual(self.store.failures("p")[0]["task"], "task")

    def test_experience_context(self):
        self.store.add_experience("p", "ctx", "lesson")
        self.assertEqual(self.store.experience("p")[0]["context"], "ctx")

    def test_query_failure(self):
        self.store.add_failure("p", "ROS2 QoS", "error")
        self.assertTrue(self.store.query("p", "QoS"))

    def test_query_experience(self):
        self.store.add_experience("p", "launch build", "lesson")
        self.assertTrue(self.store.query("p", "build"))

    def test_query_case_insensitive(self):
        self.store.add_decision("p", "Socket", "c", "r")
        self.assertTrue(self.store.query("p", "socket"))

    def test_query_multiword(self):
        self.store.add_decision("p", "Socket通信", "c", "r")
        self.assertTrue(self.store.query("p", "Socket 通信"))

    def test_persist_failures(self):
        self.store.add_failure("p", "t", "e")
        second = ProjectMemoryStore(self.store.path)
        self.assertEqual(second.failures("p")[0]["error"], "e")

    def test_persist_experience(self):
        self.store.add_experience("p", "c", "l")
        second = ProjectMemoryStore(self.store.path)
        self.assertEqual(second.experience("p")[0]["lesson"], "l")

    def test_store_initializes(self):
        self.assertIn("decisions", self.store.data)
        self.assertIn("failures", self.store.data)
        self.assertIn("experience", self.store.data)

    def test_decisions_empty_before_add(self):
        self.assertEqual(self.store.decisions("missing"), [])

    def test_failures_empty_before_add(self):
        self.assertEqual(self.store.failures("missing"), [])

    def test_experience_empty_before_add(self):
        self.assertEqual(self.store.experience("missing"), [])

    def test_add_decision_append(self):
        self.store.add_decision("p", "a", "c", "r")
        self.store.add_decision("p", "b", "c", "r")
        self.assertEqual(len(self.store.decisions("p")), 2)

    def test_add_failure_append(self):
        self.store.add_failure("p", "a", "e")
        self.store.add_failure("p", "b", "e")
        self.assertEqual(len(self.store.failures("p")), 2)

    def test_add_experience_append(self):
        self.store.add_experience("p", "a", "l")
        self.store.add_experience("p", "b", "l")
        self.assertEqual(len(self.store.experience("p")), 2)

    def test_query_returns_list(self):
        self.store.add_decision("p", "t", "c", "r")
        self.assertIsInstance(self.store.query("p", "t"), list)

    def test_query_no_project_records(self):
        self.store.add_decision("other", "t", "c", "r")
        self.assertEqual(self.store.query("p", "t"), [])

    def test_all_decisions_no_filter(self):
        self.store.add_decision("a", "t", "c", "r")
        self.store.add_decision("b", "t", "c", "r")
        self.assertEqual(len(self.store.decisions()), 2)

    def test_all_failures_no_filter(self):
        self.store.add_failure("a", "t", "e")
        self.store.add_failure("b", "t", "e")
        self.assertEqual(len(self.store.failures()), 2)

    def test_all_experience_no_filter(self):
        self.store.add_experience("a", "c", "l")
        self.store.add_experience("b", "c", "l")
        self.assertEqual(len(self.store.experience()), 2)

    def test_persistence_path(self):
        self.assertEqual(self.store.path.suffix, ".json")

    def test_query_all_three_types(self):
        self.store.add_decision("p", "设计", "c", "r")
        self.store.add_failure("p", "bug", "e")
        self.store.add_experience("p", "build", "l")
        results = self.store.query("p", "设计 bug build")
        self.assertEqual(len(results), 3)

    def test_decision_topic_field(self):
        self.store.add_decision("p", "topic", "choice", "reason")
        self.assertEqual(self.store.decisions("p")[0]["topic"], "topic")

    def test_failure_error_field(self):
        self.store.add_failure("p", "task", "error", "fix")
        self.assertEqual(self.store.failures("p")[0]["error"], "error")

    def test_experience_lesson_field(self):
        self.store.add_experience("p", "context", "lesson")
        self.assertEqual(self.store.experience("p")[0]["lesson"], "lesson")

    def test_query_decision_reason(self):
        self.store.add_decision("p", "topic", "choice", "reason text")
        self.assertIn("reason", self.store.query("p", "reason")[0]["reason"])

    def test_query_empty_question(self):
        self.store.add_decision("p", "topic", "choice", "reason")
        self.assertEqual(self.store.query("p", ""), [])

    def test_store_save_creates_file(self):
        self.store.add_decision("p", "t", "c", "r")
        self.assertTrue(self.store.path.exists())


if __name__ == "__main__":
    unittest.main()
