import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from planner.planning_decider import decide
from planner.planning_stats import savings_from_levels
from planner.task_analyzer import (
    analyze_task,
    detect_action_keywords,
    detect_file_paths,
    detect_output_requirements,
    detect_task_list,
)
from planner.task_intent import classify_intent


class TaskAnalyzerTests(unittest.TestCase):
    def test_detect_numbered_list(self):
        self.assertTrue(detect_task_list("1. a\n2. b"))

    def test_detect_chinese_steps(self):
        self.assertTrue(detect_task_list("第一步 a\n第二步 b"))

    def test_no_list(self):
        self.assertFalse(detect_task_list("优化机器人系统"))

    def test_action_keywords(self):
        self.assertIn("修改", detect_action_keywords("修改代码"))

    def test_file_paths(self):
        self.assertIn("src/main.py", detect_file_paths("修改 src/main.py"))

    def test_output_requirements(self):
        self.assertTrue(detect_output_requirements("运行测试"))

    def test_analyze_task(self):
        features = analyze_task("1. 修改 src/main.py\n2. 运行测试")
        self.assertTrue(features["has_list"])
        self.assertTrue(features["files"])

    def test_no_action_keywords(self):
        self.assertEqual(detect_action_keywords("hello"), [])

    def test_no_file_paths(self):
        self.assertEqual(detect_file_paths("hello"), [])

    def test_no_output_requirements(self):
        self.assertFalse(detect_output_requirements("hello"))

    def test_analyze_task_without_list(self):
        features = analyze_task("优化机器人系统")
        self.assertFalse(features["has_list"])


class TaskIntentTests(unittest.TestCase):
    def test_explicit_intent(self):
        features = analyze_task("1. 修改 src/main.py\n2. 运行测试")
        self.assertEqual(classify_intent(features), "explicit")

    def test_semi_intent(self):
        features = analyze_task("1. 改通信\n2. 加日志")
        self.assertEqual(classify_intent(features), "semi")

    def test_goal_intent(self):
        features = analyze_task("我要做机器人系统")
        self.assertEqual(classify_intent(features), "goal")


class PlanningDeciderTests(unittest.TestCase):
    def test_direct_execute(self):
        result = decide("1. 修改 src/main.py\n2. 运行测试")
        self.assertEqual(result["planning_level"], 0)
        self.assertEqual(result["mode"], "direct_execute")
        self.assertEqual(result["workflow"], "direct")

    def test_task_organization(self):
        result = decide("1. 改通信\n2. 加日志\n3. 提高稳定性")
        self.assertEqual(result["planning_level"], 1)
        self.assertEqual(result["mode"], "task_organization")

    def test_full_planning(self):
        result = decide("我要做一个工业机器人智能体系统")
        self.assertEqual(result["planning_level"], 2)
        self.assertEqual(result["mode"], "full_workflow")

    def test_agents_for_level(self):
        self.assertIn("coder", decide("1. 修改 src/main.py")["agents"])
        self.assertIn("architect", decide("我要做系统")["agents"])

    def test_confidence_in_range(self):
        result = decide("1. 修改代码")
        self.assertGreaterEqual(result["confidence"], 0)
        self.assertLessEqual(result["confidence"], 1)

    def test_full_workflow_mapping(self):
        self.assertEqual(decide("我要做系统")["workflow"], "developer")

    def test_organize_workflow_mapping(self):
        self.assertEqual(decide("1. 改通信\n2. 加日志")["workflow"], "organize")

    def test_reason_present(self):
        self.assertTrue(decide("优化系统")["reason"])


class PlanningStatsTests(unittest.TestCase):
    def test_savings(self):
        stats = savings_from_levels([0, 0, 1, 2])
        self.assertEqual(stats["total"], 4)
        self.assertEqual(stats["direct"], 2)
        self.assertGreater(stats["estimated_savings"], 0)

    def test_ratios_sum(self):
        stats = savings_from_levels([0, 1, 2])
        self.assertAlmostEqual(stats["direct_ratio"] + stats["organize_ratio"] + stats["full_ratio"], 1.0)

    def test_empty_levels(self):
        stats = savings_from_levels([])
        self.assertEqual(stats["total"], 1)


if __name__ == "__main__":
    unittest.main()
