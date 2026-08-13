import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from providers.mock_provider import MockProvider
from providers.status import ProviderStatus, emoji_for


class MockProviderTests(unittest.TestCase):
    def test_normal_balance(self):
        provider = MockProvider(balance="normal")
        self.assertEqual(provider.get_balance(), "normal")

    def test_low_balance(self):
        provider = MockProvider(balance="low")
        self.assertEqual(provider.get_balance(), "low")

    def test_api_error(self):
        provider = MockProvider(error=RuntimeError("boom"))
        with self.assertRaises(RuntimeError):
            provider.chat([{"role": "user", "content": "hi"}])

    def test_health_available(self):
        provider = MockProvider(status="available")
        self.assertEqual(provider.health_check()["status"], "available")

    def test_health_unavailable(self):
        provider = MockProvider(status="unavailable")
        self.assertEqual(provider.health_check()["status"], "unavailable")


class StatusTests(unittest.TestCase):
    def test_status_to_dict(self):
        status = ProviderStatus("deepseek", balance_status="normal")
        self.assertEqual(status.to_dict()["balance_status"], "normal")

    def test_emoji_available(self):
        self.assertEqual(emoji_for("available"), "🟢")

    def test_emoji_warning(self):
        self.assertEqual(emoji_for("warning"), "🟡")

    def test_emoji_unavailable(self):
        self.assertEqual(emoji_for("unavailable"), "🔴")


if __name__ == "__main__":
    unittest.main()
