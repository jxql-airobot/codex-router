import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from desktop.ai_status_window import render_status
from desktop.dashboard_launcher import build_dashboard_command, dashboard_path
from desktop.shortcut_creator import build_shortcut_command


class StatusWindowTests(unittest.TestCase):
    def test_contains_provider_names(self):
        text = render_status()
        self.assertIn("DeepSeek", text)
        self.assertIn("Qwen", text)
        self.assertIn("GLM", text)

    def test_contains_emoji(self):
        text = render_status()
        self.assertIn("🟢", text)
        self.assertIn("🟡", text)
        self.assertIn("🔴", text)

    def test_custom_providers(self):
        text = render_status([{"name": "X", "status": "available"}])
        self.assertIn("X", text)

    def test_unknown_status_emoji(self):
        text = render_status([{"name": "Y", "status": "unknown"}])
        self.assertIn("⚪", text)

    def test_default_has_four_providers(self):
        self.assertEqual(len(render_status().splitlines()) - 1, 4)


class ShortcutCreatorTests(unittest.TestCase):
    def test_command_contains_paths(self):
        command = build_shortcut_command("python", r"C:\Desktop\AI.lnk", "desktop/launcher.py")
        self.assertIn("WScript.Shell", command)
        self.assertIn("AI.lnk", command)

    def test_command_contains_arguments(self):
        command = build_shortcut_command("python", "x.lnk", "desktop/launcher.py")
        self.assertIn("desktop/launcher.py", command)

    def test_command_no_arguments(self):
        command = build_shortcut_command("python", "x.lnk")
        self.assertIn("x.lnk", command)


class DashboardLauncherTests(unittest.TestCase):
    def test_dashboard_path(self):
        self.assertTrue(dashboard_path().name.endswith("index.html"))

    def test_build_command(self):
        command = build_dashboard_command()
        self.assertIn("index.html", command)

    def test_dashboard_path_absolute(self):
        self.assertTrue(dashboard_path().is_absolute())


if __name__ == "__main__":
    unittest.main()
