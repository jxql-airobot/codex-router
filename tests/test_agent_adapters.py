import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agent_registry import load_enabled_agents
from agents.base_agent import BaseAgent
from config_loader import load_config


class AgentAdapterTests(unittest.TestCase):
    def test_enabled_agents_are_loaded(self):
        config = load_config(ROOT / "config.yaml")
        agents = load_enabled_agents(config)
        self.assertIn("codex", agents)
        self.assertIn("deepseek", agents)
        self.assertNotIn("claude", agents)
        self.assertNotIn("gemini", agents)
        self.assertNotIn("local", agents)

    def test_loaded_agents_are_base_agents(self):
        config = load_config(ROOT / "config.yaml")
        agents = load_enabled_agents(config)
        for agent in agents.values():
            self.assertIsInstance(agent, BaseAgent)

    def test_codex_adapter_name(self):
        config = load_config(ROOT / "config.yaml")
        agents = load_enabled_agents(config)
        self.assertEqual(agents["codex"].name, "codex")


if __name__ == "__main__":
    unittest.main()
