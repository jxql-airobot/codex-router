import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from classifier import classify
from config_loader import load_config
from launcher.codex_auto import parse_launcher_args, should_route
from launcher.model_runner import build_command
from model_selector import select


CONFIG = load_config(ROOT / "config.yaml")


def make_selection(task, override=None):
    result = classify(task)
    return select(result.score, CONFIG, override=override)


class ArgParsingTests(unittest.TestCase):
    def test_flash_override(self):
        args = parse_launcher_args(["--flash", "设计系统架构"])
        self.assertEqual(args.override, "flash")
        self.assertEqual(args.task_parts, ["设计系统架构"])

    def test_codex_passthrough(self):
        args = parse_launcher_args(
            ["--add-dir", "C:\\tmp", "--search", "修改一个Python函数"]
        )
        self.assertEqual(
            args.codex_args, ["--add-dir", "C:\\tmp", "--search"]
        )
        self.assertEqual(args.task_parts, ["修改一个Python函数"])

    def test_stdin_marker_is_task(self):
        args = parse_launcher_args(["-"])
        self.assertEqual(args.task_parts, ["-"])

    def test_should_route_prompt(self):
        self.assertTrue(should_route(["修改一个Python函数"]))

    def test_should_not_route_help(self):
        self.assertFalse(should_route(["--help"]))

    def test_should_not_route_subcommand(self):
        self.assertFalse(should_route(["login"]))
        self.assertFalse(should_route(["exec", "修改一个Python函数"]))

    def test_should_route_model_option_with_task(self):
        self.assertTrue(
            should_route(["--model", "deepseek-v4-pro", "修改一个Python函数"])
        )

    def test_agent_and_direct_overrides(self):
        self.assertEqual(parse_launcher_args(["--agent", "任务"]).mode_override, "agent")
        self.assertEqual(parse_launcher_args(["--direct", "任务"]).mode_override, "direct")


class CommandBuildingTests(unittest.TestCase):
    def test_cli_flash(self):
        selection = make_selection("修改一个Python函数")
        plan = build_command(selection, "修改一个Python函数", [], CONFIG)
        self.assertIn("-m", plan.command)
        self.assertIn("deepseek-v4-flash", plan.command)
        self.assertEqual(plan.command[-1], "修改一个Python函数")

    def test_cli_pro(self):
        selection = make_selection("设计ROS2机器人Agent架构")
        plan = build_command(selection, "设计ROS2机器人Agent架构", [], CONFIG)
        self.assertIn("deepseek-v4-pro", plan.command)

    def test_forced_flash_wins(self):
        selection = make_selection("设计系统架构", override="flash")
        self.assertEqual(selection.tier, "flash")
        plan = build_command(selection, "设计系统架构", [], CONFIG)
        self.assertIn("deepseek-v4-flash", plan.command)

    def test_env_switch_sets_model_name(self):
        selection = make_selection("修改一个Python函数")
        config = load_config(ROOT / "config.yaml")
        config["launcher"]["model_switch"] = "env"
        plan = build_command(selection, "修改一个Python函数", [], config)
        self.assertNotIn("-m", plan.command)
        self.assertEqual(plan.env["MODEL_NAME"], "deepseek-v4-flash")
        self.assertEqual(plan.env["MODEL_PROVIDER"], "deepseek")

    def test_config_switch_uses_config_overrides(self):
        selection = make_selection("设计ROS2机器人Agent架构")
        config = load_config(ROOT / "config.yaml")
        config["launcher"]["model_switch"] = "config"
        plan = build_command(selection, "设计ROS2机器人Agent架构", [], config)
        self.assertIn("-c", plan.command)
        self.assertIn("model=deepseek-v4-pro", plan.command)

    def test_explicit_model_flag_is_respected(self):
        selection = make_selection("修改一个Python函数")
        plan = build_command(
            selection,
            "修改一个Python函数",
            ["-m", "custom-model"],
            CONFIG,
        )
        self.assertIn("custom-model", plan.command)
        self.assertNotIn("deepseek-v4-flash", plan.command)


if __name__ == "__main__":
    unittest.main()
