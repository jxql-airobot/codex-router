"""Generate an execution loop report."""

from __future__ import annotations

from typing import Any


def generate_report(task: str, status: str, tests: str, commit: str) -> str:
    return "\n".join(
        [
            "Execution Report",
            f"Task: {task}",
            f"Status: {status}",
            f"Tests: {tests}",
            f"Commit: {commit}",
        ]
    )
