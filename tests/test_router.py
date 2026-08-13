import unittest
from pathlib import Path

import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from classifier import DiffStats, classify
from model_selector import load_config, select
from router import parse_model_command


CONFIG = load_config(ROOT / "config.yaml")


class ClassifierTests(unittest.TestCase):
    def test_simple_bugfix_selects_flash(self):
        result = classify("修复Python报错")
        model = select(result.score, CONFIG)
        self.assertLess(result.score, 70)
        self.assertEqual(model.tier, "flash")

    def test_complex_architecture_selects_pro(self):
        result = classify("设计ROS2机器人Agent架构")
        model = select(result.score, CONFIG)
        self.assertGreaterEqual(result.score, 70)
        self.assertEqual(model.tier, "pro")

    def test_single_ros2_node_is_flash_or_medium(self):
        result = classify("增加一个ROS2节点")
        model = select(result.score, CONFIG)
        self.assertLess(result.score, 70)
        self.assertEqual(model.tier, "flash")

    def test_large_diff_boosts_score(self):
        result = classify(
            "重构通信层",
            DiffStats(files_changed=12, lines_changed=1200),
        )
        self.assertGreaterEqual(result.score, 70)

    def test_manual_override_wins(self):
        result = classify("修复Python报错")
        model = select(result.score, CONFIG, override="pro")
        self.assertEqual(model.tier, "pro")
        self.assertEqual(model.mode, "forced")


class CommandParsingTests(unittest.TestCase):
    def test_model_command_is_parsed(self):
        override, task = parse_model_command("/model pro 重构ROS2通信层")
        self.assertEqual(override, "pro")
        self.assertEqual(task, "重构ROS2通信层")

    def test_no_model_command(self):
        override, task = parse_model_command("修改一个函数")
        self.assertIsNone(override)
        self.assertEqual(task, "修改一个函数")


if __name__ == "__main__":
    unittest.main()
