"""Render a Task Report from a TaskRecord."""

from __future__ import annotations

from task_manager.manager import TaskRecord


def generate_report(record: TaskRecord) -> str:
    lines = [
        "=====================",
        "Task Report",
        "",
        f"Task: {record.task}",
        f"Model: {record.model}",
        f"Mode: {record.mode}",
        f"Changed Files: {', '.join(record.changed_files) or '-'}",
        f"Tests: {record.tests or '-'}",
        f"Commit: {record.commit or '-'}",
        f"Push: {record.push or '-'}",
        f"Status: {record.status}",
        "=====================",
    ]
    return "\n".join(lines)
