"""Top-level supervisor agent interface."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SupervisorResult:
    task: str
    plan: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, Any] = field(default_factory=dict)
    success: bool = True


class SupervisorAgent:
    name = "supervisor"

    def run(self, task: str, context: dict[str, Any] | None = None) -> SupervisorResult:
        return SupervisorResult(task=task, plan={"stages": []}, outputs=dict(context or {}))
