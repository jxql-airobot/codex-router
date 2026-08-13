import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from providers.base_provider import LLMProvider
from providers.codex_provider import CodexProvider
from providers.deepseek_provider import DeepSeekProvider


class FakeProvider(LLMProvider):
    name = "fake"

    def chat(self, messages):
        return "chat"

    def generate(self, prompt):
        return f"gen:{prompt}"


class ProviderTests(unittest.TestCase):
    def test_base_provider_has_stream_default(self):
        self.assertEqual(list(FakeProvider().stream("hi")), ["gen:hi"])

    def test_codex_provider_name(self):
        self.assertEqual(CodexProvider().name, "codex")

    def test_deepseek_provider_without_key(self):
        self.assertIn("未配置", DeepSeekProvider().generate("hi"))

    def test_deepseek_provider_chat_without_key(self):
        self.assertIn("未配置", DeepSeekProvider().chat([{"role": "user", "content": "hi"}]))


if __name__ == "__main__":
    unittest.main()
