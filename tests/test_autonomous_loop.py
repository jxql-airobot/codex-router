import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from autonomous.error_analyzer import analyze_error
from autonomous.executor import execute_step
from autonomous.git_agent import commit_work
from autonomous.loop_controller import run_loop
from autonomous.pipeline import PipelineResult, run_pipeline
from autonomous.repair_agent import repair_plan
from autonomous.report_generator import generate_report
from autonomous.test_runner import TestResult, detect_test_command, run_tests


class ExecutorTests(unittest.TestCase):
    def test_execute_step(self):
        self.assertTrue(execute_step({"name": "x"}).ok)

    def test_execute_output(self):
        self.assertEqual(execute_step({"name": "hello"}).output, "hello")

    def test_execute_default_name(self):
        self.assertEqual(execute_step({}).output, "")


class TestRunnerTests(unittest.TestCase):
    def test_detect_python(self):
        self.assertEqual(detect_test_command(["Python"]), ["pytest"])

    def test_detect_ros2(self):
        self.assertEqual(detect_test_command(["ROS2"]), ["colcon", "test"])

    def test_detect_node(self):
        self.assertEqual(detect_test_command(["Node.js"]), ["npm", "test"])

    def test_run_tests(self):
        self.assertTrue(run_tests(["pytest"]).ok)

    def test_test_result(self):
        self.assertFalse(TestResult(ok=False).ok)

    def test_detect_generic(self):
        self.assertEqual(detect_test_command(["Java"]), ["pytest"])

    def test_run_tests_empty(self):
        self.assertEqual(run_tests().output, "")

    def test_run_tests_multi(self):
        self.assertEqual(run_tests(["a", "b"]).output, "a b")

    def test_detect_node_case(self):
        self.assertEqual(detect_test_command(["node.js"]), ["npm", "test"])


class ErrorAnalyzerTests(unittest.TestCase):
    def test_has_error(self):
        self.assertTrue(analyze_error("error")["has_error"])

    def test_no_error(self):
        self.assertFalse(analyze_error("")["has_error"])

    def test_summary(self):
        self.assertIn("summary", analyze_error("error"))

    def test_summary_truncated(self):
        self.assertLessEqual(len(analyze_error("x" * 500)["summary"]), 200)


class RepairAgentTests(unittest.TestCase):
    def test_repair_plan(self):
        self.assertEqual(repair_plan({"has_error": True}), ["fix"])

    def test_no_repair(self):
        self.assertEqual(repair_plan({"has_error": False}), [])

    def test_repair_plan_list(self):
        self.assertIsInstance(repair_plan({"has_error": True}), list)


class LoopControllerTests(unittest.TestCase):
    def test_success_loop(self):
        self.assertTrue(run_loop(lambda: type("R", (), {"ok": True})(), max_retry=3))

    def test_fail_loop(self):
        self.assertFalse(run_loop(lambda: type("R", (), {"ok": False})(), max_retry=3))

    def test_loop_zero_retries(self):
        self.assertFalse(run_loop(lambda: type("R", (), {"ok": False})(), max_retry=0))


class PipelineTests(unittest.TestCase):
    def test_pipeline_success(self):
        result = run_pipeline(
            "task",
            executor=lambda: None,
            tester=lambda: TestResult(ok=True, output=""),
        )
        self.assertTrue(result.ok)
        self.assertEqual(result.attempts, 1)

    def test_pipeline_retries(self):
        result = run_pipeline(
            "task",
            executor=lambda: None,
            tester=lambda: TestResult(ok=False, output="boom"),
            max_retry=3,
        )
        self.assertFalse(result.ok)
        self.assertEqual(result.attempts, 3)

    def test_pipeline_report(self):
        result = run_pipeline(
            "task",
            executor=lambda: None,
            tester=lambda: TestResult(ok=True),
        )
        self.assertIn("success", result.report)

    def test_pipeline_failed_report(self):
        result = run_pipeline(
            "task",
            executor=lambda: None,
            tester=lambda: TestResult(ok=False, output="x"),
            max_retry=2,
        )
        self.assertIn("failed", result.report)

    def test_pipeline_history(self):
        result = run_pipeline(
            "task",
            executor=lambda: None,
            tester=lambda: TestResult(ok=True),
        )
        self.assertTrue(result.history)


class GitAgentTests(unittest.TestCase):
    def test_no_commit(self):
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run(["git", "-C", tmp, "init", "-q"], check=False)
            (Path(tmp) / "new.py").write_text("", encoding="utf-8")
            result = commit_work(tmp, commit=False)
            self.assertTrue(result.ok)
            self.assertIn("feat:", result.message)

    def test_no_changes_commit(self):
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run(["git", "-C", tmp, "init", "-q"], check=False)
            result = commit_work(tmp, commit=True)
            self.assertTrue(result.ok)
            self.assertEqual(result.message, "no changes")

    def test_commit_message_docs(self):
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run(["git", "-C", tmp, "init", "-q"], check=False)
            (Path(tmp) / "README.md").write_text("# doc", encoding="utf-8")
            result = commit_work(tmp, commit=False)
            self.assertTrue(result.message.startswith("docs:"))


class ReportGeneratorTests(unittest.TestCase):
    def test_report(self):
        text = generate_report("t", "success", "32 passed", "feat: x")
        self.assertIn("Execution Report", text)
        self.assertIn("32 passed", text)

    def test_report_commit(self):
        self.assertIn("feat: x", generate_report("t", "s", "t", "feat: x"))

    def test_report_task(self):
        self.assertIn("t", generate_report("t", "s", "t", "c"))


class EdgeCaseTests(unittest.TestCase):
    def test_analyze_unicode_error(self):
        self.assertTrue(analyze_error("错误")["has_error"])

    def test_analyze_whitespace(self):
        self.assertFalse(analyze_error("   ")["has_error"])

    def test_repair_plan_empty_error(self):
        self.assertEqual(repair_plan({}), [])

    def test_pipeline_attempts_equal_retries(self):
        result = run_pipeline("t", lambda: None, lambda: TestResult(ok=False), max_retry=4)
        self.assertEqual(result.attempts, 4)

    def test_pipeline_success_first(self):
        result = run_pipeline("t", lambda: None, lambda: TestResult(ok=True), max_retry=4)
        self.assertEqual(result.attempts, 1)

    def test_detect_python_uppercase(self):
        self.assertEqual(detect_test_command(["PYTHON"]), ["pytest"])

    def test_detect_ros2_lower(self):
        self.assertEqual(detect_test_command(["ros2"]), ["colcon", "test"])

    def test_commit_no_repo(self):
        result = commit_work(None, commit=False)
        self.assertTrue(result.ok)

    def test_report_empty_commit(self):
        self.assertIn("Commit:", generate_report("t", "s", "t", ""))

    def test_loop_runner_called(self):
        calls = []
        def runner():
            calls.append(1)
            return type("R", (), {"ok": True})()
        run_loop(runner, max_retry=5)
        self.assertEqual(len(calls), 1)

    def test_loop_failure_calls_max(self):
        calls = []
        def runner():
            calls.append(1)
            return type("R", (), {"ok": False})()
        run_loop(runner, max_retry=3)
        self.assertEqual(len(calls), 3)

    def test_pipeline_repair_present(self):
        result = run_pipeline(
            "t",
            lambda: None,
            lambda: TestResult(ok=False, output="err"),
            max_retry=2,
        )
        self.assertIn("repairs", result.history[-1])

    def test_test_result_ok_default(self):
        self.assertFalse(TestResult().ok)

    def test_execute_step_is_truthy(self):
        self.assertTrue(execute_step({"name": "x"}).ok)

    def test_error_summary_type(self):
        self.assertIsInstance(analyze_error("err")["summary"], str)

    def test_repair_plan_single(self):
        self.assertEqual(len(repair_plan({"has_error": True})), 1)

    def test_git_commit_false_does_not_modify(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = commit_work(tmp, commit=False)
            self.assertFalse((Path(tmp) / ".git").exists())


if __name__ == "__main__":
    unittest.main()
