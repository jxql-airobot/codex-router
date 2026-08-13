"""Planner agent produces a structured task plan."""

from __future__ import annotations

import json
from typing import Any

from agents.base import AgentResult, BaseAgent
from orchestrator.task_decomposer import decompose


class PlannerAgent(BaseAgent):
    name = "planner"
    description = "将用户需求拆分为结构化任务计划"
    capabilities = ["planning", "task_decomposition"]

    def execute(self, task: str, context: dict[str, Any] | str = "") -> AgentResult:
        steps = decompose(task)
        plan = {
            "goal": task,
            "tasks": [step.to_dict() for step in steps],
        }
        output = json.dumps(plan, ensure_ascii=False, indent=2)
        return AgentResult(success=True, output=output, artifacts=[plan])
