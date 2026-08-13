import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from analytics.efficiency import efficiency
from analytics.heatmap import daily_activity
from analytics.statistics import breakdowns, chinese_number, format_number, overview, token_history
from usage.models import UsageRecord
from usage.tracker import UsageTracker


class AnalyticsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.tracker = UsageTracker(Path(self.tmp.name) / "usage.db", ROOT / "config" / "pricing.yaml")
        self.tracker.track(
            UsageRecord(
                project="AI-Robot-Demo",
                agent="coder",
                provider="deepseek",
                model="deepseek-v4",
                input_tokens=1_000_000,
                output_tokens=500_000,
                total_tokens=1_500_000,
                commit_id="abc123",
                files_changed=5,
                tests_added=2,
                success=True,
            )
        )
        self.tracker.track(
            UsageRecord(
                project="InduAgent",
                agent="planner",
                provider="gpt",
                model="gpt",
                input_tokens=200_000,
                output_tokens=100_000,
                total_tokens=300_000,
            )
        )

    def tearDown(self):
        self.tracker.close()
        self.tmp.cleanup()

    def test_format_number_k(self):
        self.assertEqual(format_number(1000), "1.0K")

    def test_format_number_m(self):
        self.assertEqual(format_number(1_000_000), "1.0M")

    def test_format_number_b(self):
        self.assertEqual(format_number(1_000_000_000), "1.0B")

    def test_chinese_number_yi(self):
        self.assertEqual(chinese_number(100_000_000), "1.0亿")

    def test_chinese_number_wan(self):
        self.assertEqual(chinese_number(10_000), "1.0万")

    def test_overview(self):
        data = overview(self.tracker)
        self.assertEqual(data["total_tokens"], 1_800_000)

    def test_breakdowns_projects(self):
        data = breakdowns(self.tracker)
        self.assertEqual(data["projects"][0]["name"], "AI-Robot-Demo")

    def test_breakdowns_models(self):
        data = breakdowns(self.tracker)
        self.assertEqual(data["models"][0]["name"], "deepseek-v4")

    def test_breakdowns_agents(self):
        data = breakdowns(self.tracker)
        self.assertEqual(data["agents"][0]["name"], "coder")

    def test_token_history(self):
        history = token_history(self.tracker)
        self.assertGreaterEqual(len(history), 2)
        self.assertIn("tokens", history[0])

    def test_efficiency(self):
        result = efficiency(self.tracker)
        self.assertEqual(result["commits"], 1)
        self.assertEqual(result["files_changed"], 5)
        self.assertEqual(result["tests_added"], 2)

    def test_efficiency_tokens_per_commit(self):
        result = efficiency(self.tracker)
        self.assertGreater(result["tokens_per_commit"], 0)

    def test_heatmap_has_days(self):
        rows = daily_activity(self.tracker, days=10)
        self.assertEqual(len(rows), 10)

    def test_heatmap_date_format(self):
        rows = daily_activity(self.tracker, days=1)
        self.assertEqual(rows[0]["date"], date.today().isoformat())


if __name__ == "__main__":
    unittest.main()
