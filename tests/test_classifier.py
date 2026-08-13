import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from classification.complexity import agents_for_score, score_complexity
from classification.intent import classify_intent
from classification.task_classifier import classify_task


class IntentTests(unittest.TestCase):
    def test_development(self):
        self.assertEqual(classify_intent("添加功能")["type"], "development")

    def test_architecture(self):
        self.assertEqual(classify_intent("设计系统")["type"], "architecture")

    def test_debug(self):
        self.assertEqual(classify_intent("修复报错")["type"], "debug")

    def test_documentation(self):
        self.assertEqual(classify_intent("更新README")["type"], "documentation")

    def test_research(self):
        self.assertEqual(classify_intent("写论文")["type"], "research")

    def test_robotics_domain(self):
        self.assertEqual(classify_intent("ROS2导航")["domain"], "robotics")

    def test_web_domain(self):
        self.assertEqual(classify_intent("前端页面")["domain"], "web")

    def test_data_domain(self):
        self.assertEqual(classify_intent("数据分析")["domain"], "data")

    def test_paper_domain(self):
        self.assertEqual(classify_intent("写论文")["domain"], "paper")

    def test_workflow_mapping(self):
        self.assertEqual(classify_intent("添加功能")["workflow"], "developer")
        self.assertEqual(classify_intent("修复报错")["workflow"], "debug")

    def test_general_domain(self):
        self.assertEqual(classify_intent("随便写点东西")["domain"], "general")

    def test_unknown_type_defaults_development(self):
        self.assertEqual(classify_intent("做点事情")["type"], "development")

    def test_development_workflow(self):
        self.assertEqual(classify_intent("添加功能")["workflow"], "developer")

    def test_research_workflow(self):
        self.assertEqual(classify_intent("写论文")["workflow"], "research")

    def test_architecture_workflow(self):
        self.assertEqual(classify_intent("设计系统")["workflow"], "architecture")


class ComplexityTests(unittest.TestCase):
    def test_score_is_0_to_10(self):
        score = score_complexity("修改README")
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 10)

    def test_simple_single_agent(self):
        self.assertEqual(agents_for_score(2), ["coder"])

    def test_medium_two_agents(self):
        self.assertEqual(agents_for_score(5), ["planner", "coder"])

    def test_complex_full_team(self):
        self.assertEqual(
            agents_for_score(9),
            ["planner", "coder", "tester", "reviewer"],
        )

    def test_boundary_3(self):
        self.assertEqual(agents_for_score(3), ["coder"])

    def test_boundary_4(self):
        self.assertEqual(agents_for_score(4), ["planner", "coder"])

    def test_boundary_7(self):
        self.assertEqual(agents_for_score(7), ["planner", "coder"])

    def test_boundary_8(self):
        self.assertEqual(
            agents_for_score(8),
            ["planner", "coder", "tester", "reviewer"],
        )


class TaskClassifierTests(unittest.TestCase):
    def test_result_has_keys(self):
        result = classify_task("设计ROS2机器人控制架构")
        for key in ("type", "domain", "complexity", "recommended_workflow", "recommended_agents", "project"):
            self.assertIn(key, result)

    def test_project_from_context(self):
        result = classify_task("修改代码", {"project_name": "AI-Robot-Demo"})
        self.assertEqual(result["project"], "AI-Robot-Demo")

    def test_architecture_complexity_is_high(self):
        result = classify_task("设计ROS2机器人Agent系统架构")
        self.assertGreaterEqual(result["complexity"], 8)

    def test_documentation_workflow(self):
        self.assertEqual(classify_task("更新README文档")["recommended_workflow"], "document")

    def test_debug_workflow(self):
        self.assertEqual(classify_task("修复报错")["recommended_workflow"], "debug")

    def test_research_workflow(self):
        self.assertEqual(classify_task("写论文")["recommended_workflow"], "research")


if __name__ == "__main__":
    unittest.main()
