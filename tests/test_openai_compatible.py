import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from providers.openai_provider import OpenAIProvider


class OpenAICompatibleTests(unittest.TestCase):
    def test_missing_key_returns_hint(self):
        provider = OpenAIProvider()
        provider.api_key = ""
        self.assertIn("未配置", provider.chat([{"role": "user", "content": "hi"}]))

    @patch("urllib.request.urlopen")
    def test_chat_returns_content(self, mock_urlopen):
        provider = OpenAIProvider()
        provider.api_key = "test-key"
        fake = type(
            "R",
            (),
            {"read": lambda self: json.dumps(
                {"choices": [{"message": {"content": "你好"}}]}
            ).encode("utf-8")},
        )()
        mock_urlopen.return_value.__enter__ = lambda self: fake
        mock_urlopen.return_value.__exit__ = lambda *args: False
        self.assertEqual(
            provider.chat([{"role": "user", "content": "hi"}], model="gpt-4.1"),
            "你好",
        )

    @patch("urllib.request.urlopen")
    def test_chat_sends_bearer_header(self, mock_urlopen):
        provider = OpenAIProvider()
        provider.api_key = "secret"
        fake = type(
            "R",
            (),
            {"read": lambda self: json.dumps(
                {"choices": [{"message": {"content": "ok"}}]}
            ).encode("utf-8")},
        )()
        mock_urlopen.return_value.__enter__ = lambda self: fake
        mock_urlopen.return_value.__exit__ = lambda *args: False
        provider.chat([{"role": "user", "content": "hi"}])
        request = mock_urlopen.call_args[0][0]
        self.assertEqual(request.get_header("Authorization"), "Bearer secret")


if __name__ == "__main__":
    unittest.main()
