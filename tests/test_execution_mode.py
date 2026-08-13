import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config_loader import load_config
from launcher.agent_runner import build_agent_steps, build_step_command
from launcher.execution_mode import determine_execution_mode, load_roles


CONFIG = load_config(ROOT / "config.yaml")


class ExecutionModeTests(unittest.TestCase):
    def test_low_score_is_direct(self):
        self.assertEqual(determine_execution_mode(20, CONFIG), "direct")

    def test_mid_score_is_enhanced(self):
        self.assertEqual(determine_execution_mode(50, CONFIG), "enhanced")

    def test_high_score_is_agent(self):
        self.assertEqual(determine_execution_mode(85, CONFIG), "agent")

    def test_direct_override(self):
        self.assertEqual(
            determine_execution_mode(85, CONFIG, override="direct"), "direct"
        )

    def test_agent_override(self):
        self.assertEqual(
            determine_execution_mode(20, CONFIG, override="agent"), "agent"
        )

    def test_roles_are_ordered(self):
        roles = load_roles(CONFIG)
        self.assertEqual(
            [role.name for role in roles],
            ["planner", "coder", "tester", "reviewer"],
        )


class AgentPipelineTests(unittest.TestCase):
    def test_build_agent_steps(self):
        steps = build_agent_steps("设计ROS2机器人Agent系统架构", CONFIG)
        self.assertEqual(len(steps), 4)
        self.assertIn("Planner Agent", steps[0].prompt)
        self.assertIn("当前任务", steps[0].prompt)

    def test_planner_uses_pro_model(self):
        steps = build_agent_steps("设计ROS2机器人Agent系统架构", CONFIG)
        planner = steps[0]
        command = build_step_command(planner, CONFIG)
        self.assertIn("deepseek-v4-pro", command)
        self.assertIn("read-only", command)

    def test_coder_uses_flash_and_writable_sandbox(self):
        steps = build_agent_steps("设计ROS2机器人Agent系统架构", CONFIG)
        coder = steps[1]
        command = build_step_command(coder, CONFIG)
        self.assertIn("deepseek-v4-flash", command)
        self.assertIn("workspace-write", command)


if __name__ == "__main__":
    unittest.main()
