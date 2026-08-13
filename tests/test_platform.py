import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config_loader import load_config
from platform import status


class PlatformTests(unittest.TestCase):
    def test_status_lists_enabled_adapters(self):
        config = load_config(ROOT / "config.yaml")
        text = status(config)
        self.assertIn("Universal AI Engineering Platform", text)
        self.assertIn("codex", text)
        self.assertIn("deepseek", text)


if __name__ == "__main__":
    unittest.main()
