import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from providers.health_check import check_provider, chinese_warning, is_usable
from providers.mock_provider import MockProvider


class HealthCheckTests(unittest.TestCase):
    def test_check_available(self):
        status = check_provider(MockProvider(name="deepseek", status="available"))
        self.assertEqual(status.status, "available")

    def test_check_low_balance(self):
        status = check_provider(MockProvider(name="deepseek", balance="low"))
        self.assertEqual(status.balance_status, "low")

    def test_is_usable_warning(self):
        status = check_provider(MockProvider(status="warning"))
        self.assertTrue(is_usable(status))

    def test_is_not_usable_unavailable(self):
        status = check_provider(MockProvider(status="unavailable"))
        self.assertFalse(is_usable(status))

    def test_chinese_warning_contains_balance(self):
        status = check_provider(MockProvider(name="deepseek", balance="low"))
        text = chinese_warning(status, "AI-Robot-Demo开发")
        self.assertIn("余额不足", text)
        self.assertIn("AI-Robot-Demo开发", text)

    def test_error_count_increments(self):
        provider = MockProvider(error=RuntimeError("x"))
        status = check_provider(provider)
        self.assertEqual(status.status, "unavailable")
        self.assertEqual(status.error_count, 1)


if __name__ == "__main__":
    unittest.main()
