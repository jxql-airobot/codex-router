import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
import sys

sys.path.insert(0, str(ROOT))

from usage.calculator import CostCalculator
from usage.collector import UsageCollector, capture_usage, estimate_tokens
from usage.database import UsageDatabase
from usage.models import UsageRecord
from usage.tracker import UsageTracker
from usage_cli import render


class ModelsTests(unittest.TestCase):
    def test_record_defaults(self):
        record = UsageRecord()
        self.assertEqual(record.total_tokens, 0)
        self.assertEqual(record.cost, 0.0)

    def test_record_fields(self):
        record = UsageRecord(project="p", provider="deepseek", model="deepseek-v4")
        self.assertEqual(record.project, "p")
        self.assertEqual(record.provider, "deepseek")

    def test_timestamp_is_set(self):
        record = UsageRecord()
        self.assertTrue(record.timestamp)


class CalculatorTests(unittest.TestCase):
    def test_cost_calculation(self):
        calc = CostCalculator(ROOT / "config" / "pricing.yaml")
        cost = calc.calculate("deepseek-v4", 1_000_000, 500_000, 100_000)
        self.assertAlmostEqual(cost, 1.51, places=2)

    def test_unknown_model_zero_cost(self):
        calc = CostCalculator(ROOT / "config" / "pricing.yaml")
        self.assertEqual(calc.calculate("unknown", 1000, 1000), 0.0)

    def test_cache_price_included(self):
        calc = CostCalculator(ROOT / "config" / "pricing.yaml")
        cost = calc.calculate("deepseek-v4", 0, 0, 1_000_000)
        self.assertAlmostEqual(cost, 0.1, places=2)


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = UsageDatabase(Path(self.tmp.name) / "usage.db")

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_insert_and_total(self):
        self.db.insert(
            UsageRecord(
                project="demo",
                provider="deepseek",
                model="deepseek-v4",
                input_tokens=100,
                output_tokens=50,
                total_tokens=150,
                cost=1.0,
            )
        )
        self.assertEqual(self.db.total_since()["total_tokens"], 150)

    def test_breakdown_by_model(self):
        self.db.insert(UsageRecord(model="deepseek-v4", total_tokens=100, project="p", provider="d"))
        self.db.insert(UsageRecord(model="gpt", total_tokens=50, project="p", provider="g"))
        rows = self.db.breakdown("model")
        self.assertEqual(rows[0]["name"], "deepseek-v4")

    def test_recent(self):
        self.db.insert(UsageRecord(project="p", model="m", total_tokens=10))
        self.assertEqual(len(self.db.recent()), 1)

    def test_breakdown_by_project(self):
        self.db.insert(UsageRecord(project="a", model="m", total_tokens=10))
        self.db.insert(UsageRecord(project="b", model="m", total_tokens=5))
        self.assertEqual(self.db.breakdown("project")[0]["name"], "a")

    def test_breakdown_by_agent(self):
        self.db.insert(UsageRecord(agent="coder", model="m", total_tokens=10))
        self.assertEqual(self.db.breakdown("agent")[0]["name"], "coder")

    def test_empty_total(self):
        self.assertEqual(self.db.total_since()["total_tokens"], 0)

    def test_input_output_totals(self):
        self.db.insert(UsageRecord(input_tokens=70, output_tokens=30, total_tokens=100, project="p", model="m"))
        total = self.db.total_since()
        self.assertEqual(total["input_tokens"], 70)
        self.assertEqual(total["output_tokens"], 30)


class TrackerTests(unittest.TestCase):
    def test_track_sets_cost_and_total(self):
        with tempfile.TemporaryDirectory() as tmp:
            tracker = UsageTracker(Path(tmp) / "usage.db", ROOT / "config" / "pricing.yaml")
            record = tracker.track(
                UsageRecord(
                    project="p",
                    model="deepseek-v4",
                    input_tokens=1_000_000,
                    output_tokens=500_000,
                )
            )
            self.assertEqual(record.total_tokens, 1_500_000)
            self.assertGreater(record.cost, 0)
            tracker.close()


class CollectorTests(unittest.TestCase):
    def test_estimate_tokens(self):
        self.assertGreater(estimate_tokens("hello world"), 0)

    def test_collector_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            tracker = UsageTracker(Path(tmp) / "usage.db", ROOT / "config" / "pricing.yaml")
            collector = UsageCollector(tracker, project="p", provider="d", model="deepseek-v4", agent="coder")
            record = collector.record("input text here", "output text")
            self.assertGreater(record.input_tokens, 0)
            self.assertGreater(record.output_tokens, 0)
            tracker.close()

    def test_capture_usage_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            tracker = UsageTracker(Path(tmp) / "usage.db", ROOT / "config" / "pricing.yaml")
            with capture_usage(tracker, project="p", model="deepseek-v4") as collector:
                record = collector.record("hello", "world")
            self.assertGreater(record.total_tokens, 0)
            tracker.close()


class CliRenderTests(unittest.TestCase):
    def test_render_basic(self):
        text = render(detail=False)
        self.assertIn("Today Usage", text)
        self.assertIn("Tokens:", text)

    def test_render_detail(self):
        text = render(detail=True)
        self.assertIn("Model Usage", text)
        self.assertIn("Project Usage", text)


if __name__ == "__main__":
    unittest.main()
