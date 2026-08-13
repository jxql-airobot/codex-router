import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from analytics.classification import classification_stats
from usage.models import UsageRecord
from usage.tracker import UsageTracker


class ClassificationStatsTests(unittest.TestCase):
    def test_empty_stats(self):
        with tempfile.TemporaryDirectory() as tmp:
            tracker = UsageTracker(Path(tmp) / "usage.db", ROOT / "config" / "pricing.yaml")
            self.assertEqual(classification_stats(tracker), [])
            tracker.close()

    def test_task_type_distribution(self):
        with tempfile.TemporaryDirectory() as tmp:
            tracker = UsageTracker(Path(tmp) / "usage.db", ROOT / "config" / "pricing.yaml")
            tracker.track(UsageRecord(project="p", model="m", task_type="development", total_tokens=10))
            tracker.track(UsageRecord(project="p", model="m", task_type="debug", total_tokens=5))
            stats = classification_stats(tracker)
            self.assertEqual(len(stats), 2)
            self.assertEqual({row["type"] for row in stats}, {"development", "debug"})
            tracker.close()

    def test_ratio_sums_to_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            tracker = UsageTracker(Path(tmp) / "usage.db", ROOT / "config" / "pricing.yaml")
            tracker.track(UsageRecord(project="p", model="m", task_type="a", total_tokens=1))
            tracker.track(UsageRecord(project="p", model="m", task_type="b", total_tokens=1))
            stats = classification_stats(tracker)
            self.assertAlmostEqual(sum(row["ratio"] for row in stats), 1.0)
            tracker.close()

    def test_unknown_task_type(self):
        with tempfile.TemporaryDirectory() as tmp:
            tracker = UsageTracker(Path(tmp) / "usage.db", ROOT / "config" / "pricing.yaml")
            tracker.track(UsageRecord(project="p", model="m", total_tokens=1))
            stats = classification_stats(tracker)
            self.assertEqual(stats[0]["type"], "unknown")
            tracker.close()


if __name__ == "__main__":
    unittest.main()
