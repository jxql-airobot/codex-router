import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agents.planner_agent import PlannerAgent
from orchestrator.task_decomposer import decompose


class TaskDecomposerTests(unittest.TestCase):
    def test_simple_task_single_step(self):
        steps = decompose("修改README")
        self.assertEqual(len(steps), 1)
        self.assertEqual(steps[0].agent, "coder")

    def test_medium_task_two_steps(self):
        steps = decompose("重构ROS2通信模块")
        self.assertEqual(len(steps), 2)
        self.assertEqual(steps[0].agent, "planner")
        self.assertEqual(steps[1].depends_on, ["1"])

    def test_complex_task_full_team(self):
        steps = decompose("设计ROS2机器人Agent系统架构")
        self.assertEqual(len(steps), 4)
        self.assertEqual(steps[-1].agent, "reviewer")

    def test_steps_have_ids(self):
        steps = decompose("设计系统")
        self.assertTrue(all(step.id for step in steps))

    def test_step_to_dict(self):
        steps = decompose("修改README")
        data = steps[0].to_dict()
        self.assertIn("depends_on", data)
        self.assertIn("priority", data)


class PlannerAgentTests(unittest.TestCase):
    def test_returns_structured_decomposition(self):
        result = PlannerAgent().execute("设计ROS2机器人Agent系统架构", {})
        self.assertTrue(result.success)
        plan = json.loads(result.output)
        self.assertIn("goal", plan)
        self.assertEqual(len(plan["tasks"]), 4)

    def test_simple_plan_single_task(self):
        result = PlannerAgent().execute("修改README", {})
        plan = json.loads(result.output)
        self.assertEqual(len(plan["tasks"]), 1)


if __name__ == "__main__":
    unittest.main()
