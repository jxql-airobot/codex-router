import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config_loader import load_config
from orchestrator.fallback_manager import FallbackManager, TaskState
from providers.budget import BudgetManager


CONFIG = load_config(ROOT / "config.yaml")


class FallbackManagerTests(unittest.TestCase):
    def test_select_default_provider(self):
        manager = FallbackManager(CONFIG)
        self.assertEqual(manager.select("coder"), "deepseek")

    def test_select_after_failure(self):
        manager = FallbackManager(CONFIG)
        self.assertEqual(manager.select("coder", failed_provider="deepseek"), "qwen")

    def test_chain_architect(self):
        manager = FallbackManager(CONFIG)
        self.assertEqual(manager.chain("architect"), ["openai", "deepseek"])

    def test_recover_state(self):
        manager = FallbackManager(CONFIG)
        state = manager.recover("t1", "coder", ["planning"], "deepseek")
        self.assertEqual(state.next_provider, "qwen")
        self.assertEqual(state.completed_steps, ["planning"])


class TaskStateTests(unittest.TestCase):
    def test_to_dict(self):
        state = TaskState("t1", "coding", ["planning"], "deepseek", "qwen")
        data = state.to_dict()
        self.assertEqual(data["next_provider"], "qwen")
        self.assertEqual(data["completed_steps"], ["planning"])


class BudgetManagerTests(unittest.TestCase):
    def test_daily_limit(self):
        manager = BudgetManager(CONFIG)
        self.assertEqual(manager.daily_limit("openai"), 100_000_000)

    def test_warning(self):
        manager = BudgetManager(CONFIG)
        self.assertEqual(manager.check("openai", 90_000_000), "warning")

    def test_stop(self):
        manager = BudgetManager(CONFIG)
        self.assertEqual(manager.check("openai", 100_000_000), "stop")

    def test_normal(self):
        manager = BudgetManager(CONFIG)
        self.assertEqual(manager.check("openai", 10_000_000), "normal")


if __name__ == "__main__":
    unittest.main()
