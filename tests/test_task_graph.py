import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from supervisor.supervisor_agent import SupervisorAgent
from task_graph.decomposition_strategy import decide
from task_graph.subtask_decider import decide_subtasks
from task_graph.task_complexity import (
    detect_domains,
    file_count,
    has_dependency_words,
    has_user_steps,
    is_forbidden,
    is_must_decompose,
)


class TaskComplexityTests(unittest.TestCase):
    def test_detect_ros2(self):
        self.assertIn("ros2", detect_domains("增加ROS2导航功能"))

    def test_detect_rag(self):
        self.assertIn("rag", detect_domains("构建RAG知识库"))

    def test_detect_plc(self):
        self.assertIn("plc", detect_domains("工业PLC自动化"))

    def test_file_count(self):
        self.assertEqual(file_count("修改 src/main.py config.yaml"), 2)

    def test_no_file_count(self):
        self.assertEqual(file_count("优化系统"), 0)

    def test_dependency_words(self):
        self.assertTrue(has_dependency_words("先设计架构，然后实现"))

    def test_no_dependency_words(self):
        self.assertFalse(has_dependency_words("修改代码"))

    def test_user_steps(self):
        self.assertTrue(has_user_steps("1. 修改代码\n2. 测试"))

    def test_forbidden(self):
        self.assertTrue(is_forbidden("修复登录失败"))

    def test_must(self):
        self.assertTrue(is_must_decompose("开发机器人Agent系统"))

    def test_detect_agent(self):
        self.assertIn("agent", detect_domains("构建多Agent系统"))

    def test_detect_paper(self):
        self.assertIn("paper", detect_domains("写论文实验"))

    def test_detect_web(self):
        self.assertIn("web", detect_domains("开发Web API"))

    def test_detect_data(self):
        self.assertIn("data", detect_domains("做数据分析"))

    def test_file_count_single(self):
        self.assertEqual(file_count("修改 src/main.py"), 1)

    def test_dependency_word_arch(self):
        self.assertTrue(has_dependency_words("架构设计"))

    def test_not_forbidden(self):
        self.assertFalse(is_forbidden("设计系统"))

    def test_not_must(self):
        self.assertFalse(is_must_decompose("修改配置"))


class DecompositionStrategyTests(unittest.TestCase):
    def test_simple_task_level0(self):
        result = decide("修改config.yaml里的端口号")
        self.assertEqual(result["decomposition_level"], 0)
        self.assertFalse(result["need_subtask"])

    def test_bugfix_level0(self):
        result = decide("修复Python报错")
        self.assertEqual(result["decomposition_level"], 0)

    def test_readme_level0(self):
        result = decide("更新README")
        self.assertEqual(result["decomposition_level"], 0)

    def test_user_plan_level0(self):
        result = decide("1. 修改代码\n2. 测试")
        self.assertEqual(result["decomposition_level"], 0)

    def test_multi_domain_level2(self):
        result = decide("工业机器人+RAG+ROS2")
        self.assertEqual(result["decomposition_level"], 2)
        self.assertTrue(result["need_subtask"])

    def test_must_level2(self):
        result = decide("开发一个机器人Agent系统")
        self.assertEqual(result["decomposition_level"], 2)

    def test_single_agent_multistep_level1(self):
        result = decide("增加一个ROS2节点")
        self.assertEqual(result["decomposition_level"], 1)

    def test_estimated_agents(self):
        result = decide("工业机器人+RAG+ROS2")
        self.assertGreaterEqual(result["estimated_agents"], 2)

    def test_explicit_files_level0(self):
        result = decide("修改 src/main.py 和 config.yaml")
        self.assertEqual(result["decomposition_level"], 0)

    def test_report_level0(self):
        result = decide("生成报告")
        self.assertEqual(result["decomposition_level"], 0)

    def test_dependency_level1(self):
        result = decide("先改代码再测试")
        self.assertEqual(result["decomposition_level"], 1)

    def test_cross_domain_reason(self):
        result = decide("机器人+RAG")
        self.assertIn("多领域", result["reason"])

    def test_level1_need_subtask(self):
        result = decide("增加一个ROS2节点")
        self.assertTrue(result["need_subtask"])

    def test_simple_reason(self):
        result = decide("修改配置")
        self.assertIn("无需拆解", result["reason"])

    def test_user_plan_reason(self):
        result = decide("1. 修改代码\n2. 测试")
        self.assertIn("不重复拆解", result["reason"])


class SubtaskDeciderTests(unittest.TestCase):
    def test_decide_subtasks(self):
        self.assertEqual(decide_subtasks("修改配置")["decomposition_level"], 0)

    def test_returns_need_subtask(self):
        self.assertIn("need_subtask", decide_subtasks("修改配置"))

    def test_complex_returns_agents(self):
        self.assertGreaterEqual(decide_subtasks("工业机器人+RAG+ROS2")["estimated_agents"], 2)

    def test_level1_returns_one_agent(self):
        self.assertEqual(decide_subtasks("增加一个ROS2节点")["estimated_agents"], 1)


class SupervisorIntegrationTests(unittest.TestCase):
    def test_result_has_decision(self):
        result = SupervisorAgent().run("设计系统")
        self.assertIn("decision", result.to_dict())

    def test_simple_decision_level0(self):
        result = SupervisorAgent().run("修改配置")
        self.assertEqual(result.decision["decomposition_level"], 0)

    def test_complex_decision_level2(self):
        result = SupervisorAgent().run("开发一个机器人Agent系统")
        self.assertEqual(result.decision["decomposition_level"], 2)


if __name__ == "__main__":
    unittest.main()
