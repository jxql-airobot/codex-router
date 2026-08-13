import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from project_manager.manager import ProjectManager


class ProjectManagerTests(unittest.TestCase):
    def test_register_list_and_load(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "demo"
            project.mkdir()
            (project / "README.md").write_text("# Demo\n", encoding="utf-8")
            (project / "requirements.txt").write_text("requests\n", encoding="utf-8")
            registry = Path(tmp) / "registry.json"

            manager = ProjectManager(registry_path=registry)
            record = manager.register(project)
            self.assertEqual(record.name, "demo")

            listed = manager.list()
            self.assertEqual(len(listed), 1)

            snapshot = manager.load(project)
            self.assertEqual(snapshot["project"], "demo")
            self.assertGreater(len(snapshot["rag"].store), 0)

    def test_save_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "demo"
            project.mkdir()
            (project / "README.md").write_text("# Demo\n", encoding="utf-8")
            registry = Path(tmp) / "registry.json"

            manager = ProjectManager(registry_path=registry)
            manager.register(project)
            manager.save_history(project, "feat: init")
            listed = manager.list()
            self.assertIn("feat: init", listed[0].history)


if __name__ == "__main__":
    unittest.main()
