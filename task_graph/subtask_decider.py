"""Public subtask decision facade."""

from __future__ import annotations

from task_graph.decomposition_strategy import decide


def decide_subtasks(task: str) -> dict:
    return decide(task)
