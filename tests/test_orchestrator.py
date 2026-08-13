import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agents.base import AgentResult, BaseAgent
from orchestrator.agent_manager import AgentManager
from orchestrator.supervisor import Supervisor
from orchestrator.task_queue import Task, TaskQueue
from orchestrator.workflow import Workflow, load_workflow


class OkAgent(BaseAgent):
    name = "ok"

    def execute(self, task, context=""):
        return AgentResult(success=True, output=f"ok:{task}")


class FailAgent(BaseAgent):
    name = "fail"

    def execute(self, task, context=""):
        return AgentResult(success=False, output="failed")


class TaskQueueTests(unittest.TestCase):
    def test_push_pop(self):
        queue = TaskQueue()
        queue.push(Task("1", "t", "a"))
        self.assertEqual(queue.pop().id, "1")
        self.assertIsNone(queue.pop())

    def test_update(self):
        queue = TaskQueue()
        queue.push(Task("1", "t", "a"))
        queue.update("1", "completed", {"out": "x"})
        self.assertEqual(queue.snapshot()[0]["status"], "completed")


class AgentManagerTests(unittest.TestCase):
    def test_register_and_get(self):
        manager = AgentManager()
        manager.register(OkAgent())
        self.assertEqual(manager.get("ok").name, "ok")

    def test_unknown_agent_raises(self):
        manager = AgentManager()
        with self.assertRaises(KeyError):
            manager.get("missing")

    def test_describe(self):
        manager = AgentManager()
        manager.register(OkAgent())
        self.assertEqual(manager.describe()[0]["name"], "ok")


class WorkflowTests(unittest.TestCase):
    def test_load_workflow(self):
        with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as handle:
            handle.write("workflow:\n  - ok\n  - fail\nretry:\n  enabled: true\n  max_round: 2\n")
            path = handle.name
        workflow = load_workflow(path)
        self.assertEqual(workflow.steps, ["ok", "fail"])
        self.assertTrue(workflow.retry_enabled)
        self.assertEqual(workflow.max_round, 2)


class SupervisorTests(unittest.TestCase):
    def test_successful_run(self):
        manager = AgentManager()
        manager.register(OkAgent())
        run = Supervisor(manager).run("task", Workflow(steps=["ok"]))
        self.assertTrue(run.success)
        self.assertEqual(run.outputs["ok"], "ok:task")

    def test_failed_run_without_retry(self):
        manager = AgentManager()
        manager.register(FailAgent())
        run = Supervisor(manager).run("task", Workflow(steps=["fail"]))
        self.assertFalse(run.success)

    def test_retry_keeps_history(self):
        manager = AgentManager()
        manager.register(FailAgent())
        run = Supervisor(manager).run("task", Workflow(steps=["fail"], retry_enabled=True, max_round=3))
        self.assertEqual(len(run.history), 3)
        self.assertFalse(run.success)


if __name__ == "__main__":
    unittest.main()
