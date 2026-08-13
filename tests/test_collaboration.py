import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from launcher.collaboration import (
    AgentOutput,
    TaskAssignment,
    detect_file_conflicts,
    merge_outputs,
    plan_parallel_tasks,
    run_parallel,
)
from launcher.execution_mode import AgentRole


ROLES = [
    AgentRole("research", "pro", "read-only", "研究"),
    AgentRole("coding", "flash", "workspace-write", "编码"),
    AgentRole("testing", "flash", "workspace-write", "测试"),
]


class CollaborationTests(unittest.TestCase):
    def test_plan_parallel_tasks(self):
        assignments = plan_parallel_tasks("实现用户系统", ROLES)
        self.assertEqual(len(assignments), 3)
        self.assertEqual(assignments[0].agent, "research")

    def test_run_parallel(self):
        assignments = [TaskAssignment("a", "t"), TaskAssignment("b", "t")]

        def worker(assignment):
            return AgentOutput(agent=assignment.agent, output=f"done {assignment.agent}")

        outputs = run_parallel(assignments, worker, max_workers=2)
        self.assertEqual(sorted(o.agent for o in outputs), ["a", "b"])

    def test_merge_outputs(self):
        outputs = [AgentOutput("a", "A"), AgentOutput("b", "B")]
        merged = merge_outputs(outputs)
        self.assertIn("## a", merged)
        self.assertIn("## b", merged)

    def test_detect_file_conflicts(self):
        outputs = [
            AgentOutput("a", "", changed_files=["x.py", "y.py"]),
            AgentOutput("b", "", changed_files=["y.py"]),
        ]
        conflicts = detect_file_conflicts(outputs)
        self.assertEqual(conflicts["y.py"], ["a", "b"])


if __name__ == "__main__":
    unittest.main()
