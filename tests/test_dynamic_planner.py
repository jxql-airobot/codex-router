import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from launcher.dynamic_planner import detect_domain, plan_roles


class DynamicPlannerTests(unittest.TestCase):
    def test_detect_software_domain(self):
        self.assertEqual(detect_domain("开发用户系统"), "software")

    def test_detect_data_domain(self):
        self.assertEqual(detect_domain("做一个数据分析"), "data")

    def test_detect_paper_domain(self):
        self.assertEqual(detect_domain("写一篇论文"), "paper")

    def test_detect_ros2_domain(self):
        self.assertEqual(detect_domain("增加ROS2导航"), "ros2")

    def test_software_team(self):
        roles = plan_roles("开发用户系统")
        names = [role.name for role in roles]
        self.assertIn("backend", names)
        self.assertIn("frontend", names)
        self.assertIn("requirement", names)

    def test_roles_have_instructions(self):
        roles = plan_roles("写论文")
        self.assertTrue(all(role.instructions for role in roles))


if __name__ == "__main__":
    unittest.main()
