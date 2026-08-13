import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from autonomous.error_analyzer import analyze_error
from autonomous.executor import execute_step
from autonomous.loop_controller import run_loop
from autonomous.repair_agent import repair_plan
from autonomous.test_runner import run_tests
from code_graph.dependency_graph import build_graph
from code_graph.impact_analysis import analyze_impact
from code_graph.indexer import index_project
from code_graph.parser import parse_file
from experiment.experiment_agent import run_experiment
from experiment.parameter_manager import load_parameters
from experiment.report_generator import generate_report
from experiment.result_collector import collect_results
from memory.decision_memory import DecisionRecord
from memory.experience_memory import ExperienceRecord
from memory.failure_memory import FailureRecord
from memory.project_memory import ProjectMemory
from project_agents.role_loader import load_roles
from project_agents.team_manager import load_team
from supervisor.supervisor_agent import SupervisorAgent, SupervisorResult


class SupervisorSkeletonTests(unittest.TestCase):
    def test_supervisor_run(self):
        result = SupervisorAgent().run("task")
        self.assertIsInstance(result, SupervisorResult)
        self.assertEqual(result.task, "task")


class AutonomousSkeletonTests(unittest.TestCase):
    def test_execute_step(self):
        self.assertTrue(execute_step({"name": "x"}).ok)

    def test_run_tests(self):
        self.assertTrue(run_tests(["pytest"]).ok)

    def test_analyze_error(self):
        self.assertTrue(analyze_error("error")["has_error"])

    def test_repair_plan(self):
        self.assertEqual(repair_plan({"has_error": True}), ["fix"])

    def test_run_loop_stops(self):
        self.assertFalse(run_loop(lambda: type("R", (), {"ok": False})(), max_retry=3))


class MemorySkeletonTests(unittest.TestCase):
    def test_records(self):
        self.assertEqual(DecisionRecord("t", "c", "r").choice, "c")
        self.assertEqual(FailureRecord("t", "e").error, "e")
        self.assertEqual(ExperienceRecord("c", "l").lesson, "l")
        self.assertEqual(ProjectMemory("p").project, "p")


class CodeGraphSkeletonTests(unittest.TestCase):
    def test_parse_file(self):
        self.assertEqual(parse_file("a.py")["path"], "a.py")

    def test_build_graph(self):
        self.assertIn("edges", build_graph([]))

    def test_impact(self):
        self.assertEqual(analyze_impact("a.py", {}), [])

    def test_index(self):
        self.assertEqual(index_project(".")["root"], ".")


class ExperimentSkeletonTests(unittest.TestCase):
    def test_experiment(self):
        self.assertEqual(run_experiment({})["status"], "pending")

    def test_parameters(self):
        self.assertEqual(load_parameters("p.yaml")["path"], "p.yaml")

    def test_collect(self):
        self.assertEqual(collect_results({})["run"], {})

    def test_report(self):
        self.assertEqual(generate_report({"x": 1}), "{'x': 1}")


class ProjectAgentsSkeletonTests(unittest.TestCase):
    def test_team(self):
        self.assertEqual(load_team("AI-Robot-Demo", {"AI-Robot-Demo": ["Robot"]}), ["Robot"])

    def test_roles(self):
        self.assertEqual(load_roles(["a", "b"]), ["a", "b"])


if __name__ == "__main__":
    unittest.main()
