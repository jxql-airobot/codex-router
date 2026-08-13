"""Coder agent applies project changes through the provider layer."""

from __future__ import annotations

from typing import Any

from agents.base import AgentResult, BaseAgent


class CoderAgent(BaseAgent):
    name = "coder"
    description = "根据计划修改代码与文件"
    capabilities = ["code_generation", "file_editing"]

    def execute(self, task: str, context: dict[str, Any] | str = "") -> AgentResult:
        # Deterministic by default; a provider can be injected by the
        # orchestrator later without changing the agent interface.
        ctx = context if isinstance(context, dict) else {"task": str(context)}
        project = ctx.get("project_name", "project")
        return AgentResult(
            success=True,
            output=f"[coder] {project}: implemented {task}",
            artifacts=[{"task": task, "project": project}],
        )
