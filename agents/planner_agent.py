"""Planner agent produces a structured task plan."""

from __future__ import annotations

import json
from typing import Any

from agents.base import AgentResult, BaseAgent
from launcher.dynamic_planner import plan_roles


class PlannerAgent(BaseAgent):
    name = "planner"
    description = "将用户需求拆分为结构化任务计划"
    capabilities = ["planning", "task_decomposition"]

    def execute(self, task: str, context: dict[str, Any] | str = "") -> AgentResult:
        roles = plan_roles(task)
        plan = {
            "goal": task,
            "tasks": [
                {
                    "name": f"{role.name} step",
                    "agent": role.name,
                    "priority": "high" if role.model_tier == "pro" else "normal",
                }
                for role in roles
            ],
        }
        output = json.dumps(plan, ensure_ascii=False, indent=2)
        return AgentResult(success=True, output=output, artifacts=[plan])
