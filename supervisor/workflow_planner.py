"""Generate ordered tasks for a team."""

from __future__ import annotations

from typing import Any


def plan_tasks(task: str, team: list[dict[str, Any]]) -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    for index, member in enumerate(team):
        depends_on = [str(index)] if index else []
        tasks.append(
            {
                "name": f"{member['responsibility']}: {task}",
                "agent": member["name"],
                "depends_on": depends_on,
            }
        )
    return tasks
