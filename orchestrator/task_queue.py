"""Minimal task queue and task state tracking."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Task:
    id: str
    name: str
    agent: str
    payload: dict[str, Any] = field(default_factory=dict)
    status: str = "pending"
    result: dict[str, Any] = field(default_factory=dict)


class TaskQueue:
    def __init__(self) -> None:
        self._items: list[Task] = []

    def push(self, task: Task) -> None:
        self._items.append(task)

    def pop(self) -> Task | None:
        if not self._items:
            return None
        return self._items.pop(0)

    def update(self, task_id: str, status: str, result: dict[str, Any] | None = None) -> None:
        for task in self._items:
            if task.id == task_id:
                task.status = status
                if result is not None:
                    task.result = result
                return

    def snapshot(self) -> list[dict[str, Any]]:
        return [
            {
                "id": task.id,
                "name": task.name,
                "agent": task.agent,
                "status": task.status,
            }
            for task in self._items
        ]
