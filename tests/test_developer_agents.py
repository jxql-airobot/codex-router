import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agents.coder_agent import CoderAgent
from agents.git_agent import GitAgent
from agents.planner_agent import PlannerAgent
from agents.reviewer_agent import ReviewerAgent
from agents.tester_agent import TesterAgent


class PlannerAgentTests(unittest.TestCase):
    def test_returns_json_plan(self):
        result = PlannerAgent().execute("开发用户系统", {})
        self.assertTrue(result.success)
        plan = json.loads(result.output)
        self.assertIn("goal", plan)
        self.assertGreater(len(plan["tasks"]), 0)


class CoderAgentTests(unittest.TestCase):
    def test_returns_success(self):
        result = CoderAgent().execute("实现登录", {"project_name": "demo"})
        self.assertTrue(result.success)
        self.assertIn("demo", result.output)


class TesterAgentTests(unittest.TestCase):
    def test_detect_python(self):
        self.assertEqual(TesterAgent()._detect_command({"tech_stack": ["Python"]}), ["pytest"])

    def test_detect_ros2(self):
        self.assertEqual(TesterAgent()._detect_command({"tech_stack": ["ROS2"]}), ["colcon", "test"])

    def test_detect_node(self):
        self.assertEqual(TesterAgent()._detect_command({"tech_stack": ["Node.js"]}), ["npm", "test"])


class ReviewerAgentTests(unittest.TestCase):
    def test_review_report(self):
        result = ReviewerAgent().execute("重构", {"coder": "done"})
        self.assertTrue(result.success)
        self.assertIn("Review Report", result.output)


class GitAgentTests(unittest.TestCase):
    def test_empty_diff_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = GitAgent().execute("task", {"repo": tmp})
            self.assertFalse(result.success)

    def test_git_agent_detects_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "-C", str(root), "init", "-q"], check=False)
            subprocess.run(["git", "-C", str(root), "config", "user.name", "T"], check=False)
            subprocess.run(["git", "-C", str(root), "config", "user.email", "t@e.com"], check=False)
            (root / "new.py").write_text("", encoding="utf-8")
            result = GitAgent().execute("task", {"repo": tmp})
            self.assertTrue(result.success)
            self.assertIn("feat:", result.output)


if __name__ == "__main__":
    unittest.main()
