import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from memory.context_builder import build_context
from memory.project_scanner import scan_project


class ProjectScannerTests(unittest.TestCase):
    def test_empty_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            scan = scan_project(tmp)
            self.assertEqual(scan.project_name, Path(tmp).name)
            self.assertEqual(scan.tech_stack, [])
            self.assertFalse(scan.git.is_repo)
            self.assertEqual(scan.markers["README.md"], None)

    def test_python_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "requirements.txt").write_text("requests\n", encoding="utf-8")
            (root / "README.md").write_text("# Demo\n", encoding="utf-8")
            (root / "AGENTS.md").write_text("# Rules\n", encoding="utf-8")

            subprocess.run(["git", "-C", str(root), "init", "-q"], check=False)

            scan = scan_project(tmp)
            self.assertIn("Python", scan.tech_stack)
            self.assertTrue(scan.git.is_repo)
            self.assertIsNotNone(scan.markers["README.md"])
            self.assertIsNotNone(scan.markers["AGENTS.md"])

    def test_ros2_project_detects_stack(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "package.xml").write_text(
                "<package><name>demo</name></package>", encoding="utf-8"
            )
            (root / "CMakeLists.txt").write_text(
                "project(demo)\nfind_package(ament_cmake REQUIRED)",
                encoding="utf-8",
            )
            (root / "demo.launch.py").write_text("", encoding="utf-8")
            (root / "world.world").write_text("", encoding="utf-8")
            (root / "model.pt").write_bytes(b"not-a-real-model")

            scan = scan_project(tmp)
            self.assertIn("ROS2", scan.tech_stack)
            self.assertIn("Gazebo", scan.tech_stack)
            self.assertIn("YOLO", scan.tech_stack)


class ContextBuilderTests(unittest.TestCase):
    def test_context_contains_project_info(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("# ROS2 Robot\n", encoding="utf-8")
            (root / "package.xml").write_text("<package/>", encoding="utf-8")
            (root / "AGENTS.md").write_text("保持最小化修改。", encoding="utf-8")

            context = build_context(start=tmp)
            self.assertEqual(context.project_name, root.name)
            self.assertIn("ROS2", context.tech_stack)
            self.assertGreater(context.score_bonus, 0)
            self.assertIn("ROS2项目", context.bonus_reason)
            self.assertIn("保持最小化修改", context.instructions)
            self.assertIn("Project:", context.to_markdown())

    def test_context_markdown_for_prompt(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("# Demo\n", encoding="utf-8")
            context = build_context(start=tmp)
            text = context.to_markdown()
            self.assertIn("[Project Context]", text)
            self.assertIn(f"Project: {root.name}", text)


if __name__ == "__main__":
    unittest.main()
