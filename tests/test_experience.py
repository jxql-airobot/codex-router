import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from analytics.token_dashboard import cache_stats, model_stats, overview, project_stats
from desktop.notifier import notify
from project_center import add_project, list_projects, remove_project, switch_project
from project_manager.manager import ProjectManager
from task_history import TaskHistoryStore
from usage.models import UsageRecord
from usage.tracker import UsageTracker


class TokenDashboardTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.tracker = UsageTracker(Path(self.tmp.name) / "usage.db", ROOT / "config" / "pricing.yaml")
        self.tracker.track(
            UsageRecord(
                project="p",
                provider="deepseek",
                model="deepseek-v4",
                input_tokens=100,
                output_tokens=50,
                cached_tokens=10,
                total_tokens=160,
            )
        )

    def tearDown(self):
        self.tracker.close()
        self.tmp.cleanup()

    def test_overview(self):
        data = overview(self.tracker)
        self.assertEqual(data["total_tokens"], 160)
        self.assertEqual(data["cached_tokens"], 10)

    def test_model_stats(self):
        self.assertEqual(model_stats(self.tracker)[0]["name"], "deepseek-v4")

    def test_project_stats(self):
        self.assertEqual(project_stats(self.tracker)[0]["name"], "p")

    def test_cache_stats(self):
        stats = cache_stats(self.tracker)
        self.assertGreater(stats["cache_hit_rate"], 0)
        self.assertEqual(stats["saved_tokens"], 10)

    def test_overview_keys(self):
        data = overview(self.tracker)
        for key in ("input_tokens", "output_tokens", "cached_tokens", "total_tokens", "cost"):
            self.assertIn(key, data)

    def test_model_stats_list(self):
        self.assertIsInstance(model_stats(self.tracker), list)

    def test_project_stats_list(self):
        self.assertIsInstance(project_stats(self.tracker), list)

    def test_cache_stats_hit_rate_zero(self):
        empty = UsageTracker(Path(self.tmp.name) / "empty.db", ROOT / "config" / "pricing.yaml")
        stats = cache_stats(empty)
        self.assertEqual(stats["cache_hit_rate"], 0)
        empty.close()

    def test_overview_cost(self):
        self.assertGreaterEqual(overview(self.tracker)["cost"], 0)

    def test_model_cost_field(self):
        self.assertIn("cost", model_stats(self.tracker)[0])

    def test_project_tokens_field(self):
        self.assertIn("tokens", project_stats(self.tracker)[0])

    def test_cache_saved_tokens_positive(self):
        self.assertGreater(cache_stats(self.tracker)["saved_tokens"], 0)

    def test_overview_cached(self):
        self.assertEqual(overview(self.tracker)["cached_tokens"], 10)

    def test_overview_input(self):
        self.assertEqual(overview(self.tracker)["input_tokens"], 100)

    def test_overview_output(self):
        self.assertEqual(overview(self.tracker)["output_tokens"], 50)

    def test_model_stats_second(self):
        self.tracker.track(UsageRecord(project="p", model="gpt", total_tokens=10))
        self.assertEqual(model_stats(self.tracker)[0]["name"], "deepseek-v4")

    def test_project_stats_count(self):
        self.assertEqual(len(project_stats(self.tracker)), 1)

    def test_cache_stats_saved_nonnegative(self):
        self.assertGreaterEqual(cache_stats(self.tracker)["saved_tokens"], 0)

    def test_overview_zero_cost_possible(self):
        self.assertIsInstance(overview(self.tracker)["cost"], float)

    def test_model_stats_tokens_int(self):
        self.assertGreaterEqual(model_stats(self.tracker)[0]["tokens"], 0)

    def test_project_stats_cost(self):
        self.assertIn("cost", project_stats(self.tracker)[0])

    def test_overview_total_sum(self):
        data = overview(self.tracker)
        self.assertEqual(data["total_tokens"], data["input_tokens"] + data["output_tokens"] + data["cached_tokens"])

    def test_cache_hit_rate_range(self):
        rate = cache_stats(self.tracker)["cache_hit_rate"]
        self.assertGreaterEqual(rate, 0)
        self.assertLessEqual(rate, 1)


class TaskHistoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = TaskHistoryStore(Path(self.tmp.name) / "history.db")

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def test_add_and_list(self):
        self.store.add("p", "task", model="deepseek", tokens=100)
        self.assertEqual(len(self.store.list()), 1)

    def test_fields(self):
        self.store.add("p", "task", agent="coder", result="success", duration_seconds=1.5)
        row = self.store.list()[0]
        self.assertEqual(row["agent"], "coder")
        self.assertEqual(row["result"], "success")

    def test_list_limit(self):
        for i in range(5):
            self.store.add("p", f"task{i}")
        self.assertEqual(len(self.store.list(limit=3)), 3)

    def test_empty_history(self):
        self.assertEqual(self.store.list(), [])

    def test_time_field(self):
        self.store.add("p", "task")
        self.assertTrue(self.store.list()[0]["time"])

    def test_tokens_default_zero(self):
        self.store.add("p", "task")
        self.assertEqual(self.store.list()[0]["tokens"], 0)

    def test_duration_field(self):
        self.store.add("p", "task", duration_seconds=2.5)
        self.assertEqual(self.store.list()[0]["duration_seconds"], 2.5)

    def test_model_field(self):
        self.store.add("p", "task", model="qwen")
        self.assertEqual(self.store.list()[0]["model"], "qwen")

    def test_project_field(self):
        self.store.add("demo", "task")
        self.assertEqual(self.store.list()[0]["project"], "demo")

    def test_result_default_success(self):
        self.store.add("p", "task")
        self.assertEqual(self.store.list()[0]["result"], "success")

    def test_id_increment(self):
        first = self.store.add("p", "a")
        second = self.store.add("p", "b")
        self.assertGreater(second, first)


class ProjectCenterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        registry = Path(self.tmp.name) / "projects.json"
        self.patcher = patch(
            "project_center.ProjectManager",
            lambda: ProjectManager(registry_path=registry),
        )
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        self.tmp.cleanup()

    def test_add_project(self):
        project = Path(self.tmp.name) / "demo"
        project.mkdir()
        (project / "README.md").write_text("# Demo", encoding="utf-8")
        record = add_project(project)
        self.assertEqual(record["name"], "demo")

    def test_list_projects(self):
        project = Path(self.tmp.name) / "demo"
        project.mkdir()
        (project / "README.md").write_text("# Demo", encoding="utf-8")
        add_project(project)
        self.assertEqual(len(list_projects()), 1)

    def test_switch_project(self):
        project = Path(self.tmp.name) / "demo"
        project.mkdir()
        (project / "README.md").write_text("# Demo", encoding="utf-8")
        snapshot = switch_project(project)
        self.assertEqual(snapshot["project"], "demo")

    def test_remove_project(self):
        project = Path(self.tmp.name) / "demo"
        project.mkdir()
        (project / "README.md").write_text("# Demo", encoding="utf-8")
        add_project(project)
        remove_project(project)
        self.assertEqual(list_projects(), [])

    def test_add_project_returns_path(self):
        project = Path(self.tmp.name) / "demo"
        project.mkdir()
        (project / "README.md").write_text("# Demo", encoding="utf-8")
        self.assertIn("path", add_project(project))

    def test_switch_missing_project(self):
        snapshot = switch_project(Path(self.tmp.name) / "missing")
        self.assertEqual(snapshot["project"], "missing")


class NotifierTests(unittest.TestCase):
    def test_notify(self):
        self.assertIn("通知", notify("title", "message"))

    def test_notify_contains_title(self):
        self.assertIn("title", notify("title", "message"))

    def test_notify_contains_message(self):
        self.assertIn("message", notify("title", "message"))

    def test_notify_returns_string(self):
        self.assertIsInstance(notify("t", "m"), str)

    def test_notify_empty_message(self):
        self.assertIn("", notify("t", ""))


if __name__ == "__main__":
    unittest.main()
