import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config_loader import load_config
from model_router import detect_role, fallback_chain, load_provider, route_role
from providers.base import BaseProvider
from providers.deepseek_provider import DeepSeekProvider
from providers.moonshot_provider import MoonshotProvider
from providers.openai_compatible import OpenAICompatibleProvider
from providers.openai_provider import OpenAIProvider
from providers.qwen_provider import QwenProvider
from providers.zhipu_provider import ZhipuProvider


CONFIG = load_config(ROOT / "config.yaml")


class RoleDetectionTests(unittest.TestCase):
    def test_architect(self):
        self.assertEqual(detect_role("设计系统架构"), "architect")

    def test_coder(self):
        self.assertEqual(detect_role("实现功能"), "coder")

    def test_reviewer(self):
        self.assertEqual(detect_role("检查代码"), "reviewer")

    def test_researcher(self):
        self.assertEqual(detect_role("调研论文"), "researcher")

    def test_knowledge(self):
        self.assertEqual(detect_role("解析PDF文档"), "knowledge")

    def test_tester(self):
        self.assertEqual(detect_role("测试失败"), "tester")

    def test_default_coder(self):
        self.assertEqual(detect_role("随便做点事"), "coder")


class RouteRoleTests(unittest.TestCase):
    def test_coder_provider(self):
        plan = route_role("实现功能", CONFIG)
        self.assertEqual(plan["provider"], "deepseek")
        self.assertEqual(plan["model"], "deepseek-chat")

    def test_architect_provider(self):
        plan = route_role("设计系统", CONFIG)
        self.assertEqual(plan["provider"], "openai")

    def test_reviewer_provider(self):
        plan = route_role("检查代码", CONFIG)
        self.assertEqual(plan["provider"], "zhipu")

    def test_researcher_provider(self):
        plan = route_role("写论文", CONFIG)
        self.assertEqual(plan["provider"], "moonshot")

    def test_knowledge_provider(self):
        plan = route_role("解析PDF", CONFIG)
        self.assertEqual(plan["provider"], "qwen")

    def test_coder_fallback(self):
        plan = route_role("实现功能", CONFIG)
        self.assertEqual(plan["fallback"], ["deepseek", "qwen"])


class ProviderLoadingTests(unittest.TestCase):
    def test_load_openai(self):
        self.assertIsInstance(load_provider("openai"), OpenAIProvider)

    def test_load_deepseek(self):
        self.assertIsInstance(load_provider("deepseek"), DeepSeekProvider)

    def test_load_zhipu(self):
        self.assertIsInstance(load_provider("zhipu"), ZhipuProvider)

    def test_load_moonshot(self):
        self.assertIsInstance(load_provider("moonshot"), MoonshotProvider)

    def test_load_qwen(self):
        self.assertIsInstance(load_provider("qwen"), QwenProvider)

    def test_unknown_provider_raises(self):
        with self.assertRaises(KeyError):
            load_provider("unknown")


class ProviderClassTests(unittest.TestCase):
    def test_all_are_base_providers(self):
        for name in ("openai", "deepseek", "zhipu", "moonshot", "qwen"):
            self.assertIsInstance(load_provider(name), BaseProvider)

    def test_openai_name(self):
        self.assertEqual(OpenAIProvider().name, "openai")

    def test_deepseek_name(self):
        self.assertEqual(DeepSeekProvider().name, "deepseek")

    def test_zhipu_name(self):
        self.assertEqual(ZhipuProvider().name, "zhipu")

    def test_moonshot_name(self):
        self.assertEqual(MoonshotProvider().name, "moonshot")

    def test_qwen_name(self):
        self.assertEqual(QwenProvider().name, "qwen")

    def test_openai_model(self):
        self.assertEqual(OpenAIProvider().default_model, "gpt-4.1")

    def test_zhipu_model(self):
        self.assertEqual(ZhipuProvider().default_model, "glm-4")

    def test_moonshot_model(self):
        self.assertEqual(MoonshotProvider().default_model, "moonshot-v1-8k")

    def test_qwen_model(self):
        self.assertEqual(QwenProvider().default_model, "qwen-plus")


class FallbackTests(unittest.TestCase):
    def test_fallback_chain(self):
        self.assertEqual(fallback_chain("coder", CONFIG), ["deepseek", "qwen"])

    def test_no_fallback_for_other_role(self):
        self.assertEqual(fallback_chain("architect", CONFIG), [])


class ConfigTests(unittest.TestCase):
    def test_providers_present(self):
        for name in ("openai", "deepseek", "zhipu", "moonshot", "qwen"):
            self.assertIn(name, CONFIG["providers"])

    def test_role_routing_present(self):
        for role in ("architect", "coder", "reviewer", "researcher", "knowledge", "tester"):
            self.assertIn(role, CONFIG["role_routing"])

    def test_api_key_env_present(self):
        self.assertEqual(CONFIG["providers"]["qwen"]["api_key_env"], "DASHSCOPE_API_KEY")

    def test_providers_enabled(self):
        for name in ("openai", "deepseek", "zhipu", "moonshot", "qwen"):
            self.assertTrue(CONFIG["providers"][name]["enabled"])

    def test_architect_model(self):
        self.assertEqual(CONFIG["role_routing"]["architect"]["model"], "gpt-4.1")

    def test_reviewer_model(self):
        self.assertEqual(CONFIG["role_routing"]["reviewer"]["model"], "glm-4")

    def test_researcher_model(self):
        self.assertEqual(CONFIG["role_routing"]["researcher"]["model"], "moonshot-v1-8k")


class ChatTests(unittest.TestCase):
    def test_chat_without_key(self):
        provider = OpenAIProvider()
        provider.api_key = ""
        self.assertIn("未配置", provider.chat([{"role": "user", "content": "hi"}]))


if __name__ == "__main__":
    unittest.main()
