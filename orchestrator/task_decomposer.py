"""Automatic task decomposition into ordered subtasks."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from classification.task_classifier import classify_task


@dataclass
class TaskStep:
    id: str
    name: str
    agent: str
    depends_on: list[str] = field(default_factory=list)
    priority: str = "normal"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "agent": self.agent,
            "depends_on": self.depends_on,
            "priority": self.priority,
        }


def decompose(task: str, config: dict[str, Any] | None = None) -> list[TaskStep]:
    plan = classify_task(task)
    complexity = plan["complexity"]
    agents = plan["recommended_agents"]

    if complexity <= 3:
        return [
            TaskStep(
                id="1",
                name=task,
                agent=agents[0] if agents else "coder",
                priority="high",
            )
        ]

    if complexity <= 7:
        return [
            TaskStep("1", f"规划: {task}", agents[0] if agents else "planner", priority="high"),
            TaskStep("2", f"实现: {task}", "coder", depends_on=["1"], priority="normal"),
        ]

    steps = [
        TaskStep("1", f"分析: {task}", "planner", priority="high"),
        TaskStep("2", f"实现: {task}", "coder", depends_on=["1"], priority="normal"),
        TaskStep("3", f"测试: {task}", "tester", depends_on=["2"], priority="normal"),
        TaskStep("4", f"审查: {task}", "reviewer", depends_on=["3"], priority="normal"),
    ]
    return steps
