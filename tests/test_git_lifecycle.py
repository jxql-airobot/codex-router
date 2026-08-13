import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from git_manager.commit_generator import generate_commit_message
from git_manager.diff_analyzer import analyze_diff
from git_manager.operator import stage_and_commit
from git_manager.scanner import scan_git
from report.generator import generate_report
from task_manager.manager import TaskRecord


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)


class GitLifecycleTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        _git(self.root, "init", "-q")
        _git(self.root, "config", "user.name", "Test")
        _git(self.root, "config", "user.email", "test@example.com")

    def tearDown(self):
        self._tmp.cleanup()

    def test_scanner_detects_repo(self):
        (self.root / "main.py").write_text("print('hi')\n", encoding="utf-8")
        info = scan_git(self.root)
        self.assertTrue(info.is_repo)
        self.assertIn("main.py", info.modified_files)

    def test_diff_analyzer_classifies_untracked(self):
        (self.root / "new_feature.py").write_text("", encoding="utf-8")
        diff = analyze_diff(self.root)
        self.assertIn("new_feature.py", diff.untracked)
        self.assertGreater(diff.total, 0)

    def test_commit_message_feature(self):
        (self.root / "new_feature.py").write_text("", encoding="utf-8")
        diff = analyze_diff(self.root)
        self.assertTrue(generate_commit_message(diff).startswith("feat:"))

    def test_commit_message_docs(self):
        (self.root / "README.md").write_text("# doc\n", encoding="utf-8")
        diff = analyze_diff(self.root)
        self.assertTrue(generate_commit_message(diff).startswith("docs:"))

    def test_stage_and_commit(self):
        (self.root / "a.py").write_text("", encoding="utf-8")
        code, _ = stage_and_commit(self.root, "feat: add a.py")
        self.assertEqual(code, 0)
        self.assertIn("feat: add a.py", scan_git(self.root).recent_commits)

    def test_report_generator(self):
        record = TaskRecord(
            task="build",
            model="pro",
            mode="agent",
            changed_files=["a.py"],
            tests="35 passed",
            commit="feat: add a",
            push="pushed",
            status="done",
        )
        report = generate_report(record)
        self.assertIn("Task: build", report)
        self.assertIn("Tests: 35 passed", report)
        self.assertIn("Status: done", report)


if __name__ == "__main__":
    unittest.main()
