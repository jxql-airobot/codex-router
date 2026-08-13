import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from integration.codex_desktop import CodexDesktopIntegration
from integration.interceptor import Interceptor
from integration.session_manager import SessionManager
from memory.session_memory import SessionMemory


class SessionManagerTests(unittest.TestCase):
    def test_start_creates_id(self):
        manager = SessionManager()
        record = manager.start("任务", {"type": "development"})
        self.assertTrue(record.session_id)

    def test_start_sets_fields(self):
        manager = SessionManager()
        record = manager.start("任务", {"type": "debug", "project": "p", "recommended_agents": ["coder"]})
        self.assertEqual(record.task_type, "debug")
        self.assertEqual(record.project, "p")
        self.assertEqual(record.agents, ["coder"])

    def test_finish_updates_result(self):
        manager = SessionManager()
        record = manager.start("任务")
        finished = manager.finish(record.session_id, "success", tokens=10)
        self.assertEqual(finished.result, "success")
        self.assertEqual(finished.tokens, 10)

    def test_get(self):
        manager = SessionManager()
        record = manager.start("任务")
        self.assertEqual(manager.get(record.session_id).session_id, record.session_id)

    def test_snapshot(self):
        manager = SessionManager()
        manager.start("a")
        manager.start("b")
        self.assertEqual(len(manager.snapshot()), 2)


class InterceptorTests(unittest.TestCase):
    def test_intercept_returns_plan(self):
        plan = Interceptor().intercept("修改代码")
        self.assertIn("session_id", plan)
        self.assertIn("recommended_agents", plan)

    def test_intercept_classifies_type(self):
        plan = Interceptor().intercept("修复报错")
        self.assertEqual(plan["type"], "debug")

    def test_finish_returns_record(self):
        interceptor = Interceptor()
        plan = interceptor.intercept("修改代码")
        record = interceptor.finish(plan["session_id"], "success", tokens=3)
        self.assertEqual(record["result"], "success")


class CodexDesktopIntegrationTests(unittest.TestCase):
    def test_run(self):
        integration = CodexDesktopIntegration()
        plan = integration.run("添加功能")
        self.assertIn("session_id", plan)

    def test_complete(self):
        integration = CodexDesktopIntegration()
        plan = integration.run("添加功能")
        record = integration.complete(plan["session_id"], "success")
        self.assertEqual(record["result"], "success")


class SessionMemoryTests(unittest.TestCase):
    def test_add_and_latest(self):
        memory = SessionMemory()
        memory.add("a")
        memory.add("b")
        self.assertEqual(memory.latest(), ["a", "b"])

    def test_latest_limit(self):
        memory = SessionMemory()
        for task in ["a", "b", "c", "d"]:
            memory.add(task)
        self.assertEqual(memory.latest(2), ["c", "d"])


if __name__ == "__main__":
    unittest.main()
