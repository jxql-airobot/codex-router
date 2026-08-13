import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from supervisor.agent_selector import CAPABILITIES, select_agents
from supervisor.result_merger import merge_results
from supervisor.supervisor_agent import SupervisorAgent, SupervisorResult
from supervisor.task_analyzer import analyze_task
from supervisor.team_builder import build_team, model_for_agent
from supervisor.workflow_planner import plan_tasks
from team.dynamic_team import DynamicTeam
from team.task_assignment import TaskAssignment
from team.team_state import AgentState
from supervisor.team_builder import RESPONSIBILITIES


class TaskAnalyzerTests(unittest.TestCase):
    def test_simple_analysis(self):
        result = analyze_task("1. 修改 src/main.py\n2. 运行测试")
        self.assertEqual(result["planning_level"], 0)

    def test_medium_analysis(self):
        result = analyze_task("1. 改通信\n2. 加日志")
        self.assertEqual(result["planning_level"], 1)

    def test_goal_analysis(self):
        result = analyze_task("我要做工业机器人系统")
        self.assertEqual(result["planning_level"], 2)

    def test_analysis_has_project(self):
        self.assertEqual(analyze_task("修改代码", "demo")["project"], "demo")

    def test_analysis_difficulty(self):
        self.assertIn("difficulty", analyze_task("设计系统"))

    def test_analysis_mode(self):
        self.assertIn("mode", analyze_task("修改README"))

    def test_analysis_type(self):
        self.assertIn("type", analyze_task("修改README"))


class AgentSelectorTests(unittest.TestCase):
    def test_capabilities_registered(self):
        self.assertIn("RobotAgent", CAPABILITIES)
        self.assertIn("PLC_Agent", CAPABILITIES)

    def test_level0_single_coder(self):
        self.assertEqual(select_agents({"planning_level": 0, "domain": "robotics"}), ["CoderAgent"])

    def test_level1_organizer(self):
        self.assertEqual(select_agents({"planning_level": 1, "domain": "general"}), ["RAGAgent", "CoderAgent"])

    def test_level2_includes_architect(self):
        agents = select_agents({"planning_level": 2, "domain": "robotics"})
        self.assertIn("ArchitectAgent", agents)
        self.assertIn("CoderAgent", agents)
        self.assertIn("TesterAgent", agents)

    def test_robot_agent_selected(self):
        agents = select_agents({"planning_level": 2, "domain": "robotics"})
        self.assertIn("RobotAgent", agents)

    def test_plc_agent_selected(self):
        agents = select_agents({"planning_level": 2, "domain": "general", "type": "automation"})
        self.assertIn("PLC_Agent", agents)

    def test_research_agent_selected(self):
        agents = select_agents({"planning_level": 2, "domain": "paper"})
        self.assertIn("ResearchAgent", agents)

    def test_rag_agent_selected(self):
        agents = select_agents({"planning_level": 2, "domain": "general", "type": "documentation"})
        self.assertIn("RAGAgent", agents)

    def test_selection_dedup(self):
        agents = select_agents({"planning_level": 2, "domain": "robotics"})
        self.assertEqual(len(agents), len(set(agents)))

    def test_level1_only_two_agents(self):
        agents = select_agents({"planning_level": 1, "domain": "general"})
        self.assertEqual(len(agents), 2)

    def test_level0_ignores_domain(self):
        agents = select_agents({"planning_level": 0, "domain": "robotics"})
        self.assertEqual(agents, ["CoderAgent"])


class TeamBuilderTests(unittest.TestCase):
    def test_build_team(self):
        team = build_team(["CoderAgent", "TesterAgent"])
        self.assertEqual(team[0]["name"], "CoderAgent")
        self.assertIn("responsibility", team[0])

    def test_model_for_architect(self):
        self.assertEqual(model_for_agent("ArchitectAgent"), "openai")

    def test_model_for_coder(self):
        self.assertEqual(model_for_agent("CoderAgent"), "deepseek")


class WorkflowPlannerTests(unittest.TestCase):
    def test_tasks_match_team(self):
        team = build_team(["CoderAgent", "TesterAgent"])
        tasks = plan_tasks("实现功能", team)
        self.assertEqual(len(tasks), 2)

    def test_first_task_no_dependency(self):
        team = build_team(["CoderAgent"])
        tasks = plan_tasks("实现功能", team)
        self.assertEqual(tasks[0]["depends_on"], [])

    def test_second_task_dependency(self):
        team = build_team(["CoderAgent", "TesterAgent"])
        tasks = plan_tasks("实现功能", team)
        self.assertEqual(tasks[1]["depends_on"], ["1"])


class ResultMergerTests(unittest.TestCase):
    def test_merge(self):
        text = merge_results({"a": "A", "b": "B"})
        self.assertIn("## a", text)
        self.assertIn("## b", text)


class TeamModelTests(unittest.TestCase):
    def test_dynamic_team(self):
        team = DynamicTeam("p", [{"name": "x"}])
        self.assertEqual(team.project, "p")

    def test_agent_state(self):
        state = AgentState("coder", "working", "x.py", 60)
        self.assertEqual(state.to_dict()["progress"], 60)

    def test_task_assignment(self):
        task = TaskAssignment("t", "a", ["1"])
        self.assertEqual(task.status, "pending")


class SupervisorAgentTests(unittest.TestCase):
    def test_run_returns_result(self):
        result = SupervisorAgent().run("设计ROS2机器人Agent系统架构", "demo")
        self.assertIsInstance(result, SupervisorResult)
        self.assertTrue(result.success)

    def test_run_has_team(self):
        result = SupervisorAgent().run("设计系统")
        self.assertTrue(result.team)

    def test_run_has_tasks(self):
        result = SupervisorAgent().run("设计系统")
        self.assertEqual(len(result.tasks), len(result.team))

    def test_run_outputs(self):
        result = SupervisorAgent().run("修改README")
        self.assertIn("CoderAgent", result.outputs)

    def test_run_to_dict(self):
        result = SupervisorAgent().run("修改README")
        self.assertIn("team", result.to_dict())


class CapabilityCatalogTests(unittest.TestCase):
    def test_architect_capability(self):
        self.assertIn("架构", CAPABILITIES["ArchitectAgent"])

    def test_robot_capability(self):
        self.assertIn("ros2", CAPABILITIES["RobotAgent"])

    def test_rag_capability(self):
        self.assertIn("知识", CAPABILITIES["RAGAgent"])

    def test_coder_capability(self):
        self.assertIn("实现", CAPABILITIES["CoderAgent"])

    def test_tester_capability(self):
        self.assertIn("测试", CAPABILITIES["TesterAgent"])

    def test_research_capability(self):
        self.assertIn("论文", CAPABILITIES["ResearchAgent"])

    def test_plc_capability(self):
        self.assertIn("plc", CAPABILITIES["PLC_Agent"])


class ResponsibilityCatalogTests(unittest.TestCase):
    def test_architect_responsibility(self):
        self.assertIn("系统", RESPONSIBILITIES["ArchitectAgent"])

    def test_robot_responsibility(self):
        self.assertIn("ROS2", RESPONSIBILITIES["RobotAgent"])

    def test_rag_responsibility(self):
        self.assertIn("知识", RESPONSIBILITIES["RAGAgent"])

    def test_coder_responsibility(self):
        self.assertIn("代码", RESPONSIBILITIES["CoderAgent"])

    def test_tester_responsibility(self):
        self.assertIn("测试", RESPONSIBILITIES["TesterAgent"])

    def test_research_responsibility(self):
        self.assertIn("研究", RESPONSIBILITIES["ResearchAgent"])

    def test_plc_responsibility(self):
        self.assertIn("PLC", RESPONSIBILITIES["PLC_Agent"])


class ModelMappingTests(unittest.TestCase):
    def test_architect_model(self):
        self.assertEqual(model_for_agent("ArchitectAgent"), "openai")

    def test_robot_model(self):
        self.assertEqual(model_for_agent("RobotAgent"), "deepseek")

    def test_rag_model(self):
        self.assertEqual(model_for_agent("RAGAgent"), "qwen")

    def test_coder_model(self):
        self.assertEqual(model_for_agent("CoderAgent"), "deepseek")

    def test_tester_model(self):
        self.assertEqual(model_for_agent("TesterAgent"), "deepseek")

    def test_research_model(self):
        self.assertEqual(model_for_agent("ResearchAgent"), "moonshot")

    def test_plc_model(self):
        self.assertEqual(model_for_agent("PLC_Agent"), "deepseek")


class TeamIntegrationTests(unittest.TestCase):
    def test_full_team_for_robotics(self):
        result = SupervisorAgent().run("设计ROS2机器人系统", "AI-Robot-Demo")
        names = [member["name"] for member in result.team]
        self.assertIn("ArchitectAgent", names)
        self.assertIn("RobotAgent", names)
        self.assertIn("TesterAgent", names)

    def test_planning_level2_agents_order(self):
        result = SupervisorAgent().run("我要做系统")
        self.assertEqual(result.team[0]["name"], "ArchitectAgent")

    def test_simple_task_team(self):
        result = SupervisorAgent().run("1. 修改 src/main.py\n2. 运行测试")
        self.assertEqual([member["name"] for member in result.team], ["CoderAgent"])

    def test_tasks_are_assigned(self):
        result = SupervisorAgent().run("设计系统")
        self.assertEqual(result.tasks[0]["agent"], "ArchitectAgent")


if __name__ == "__main__":
    unittest.main()
