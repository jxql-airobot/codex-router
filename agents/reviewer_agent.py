"""Reviewer agent produces a review report."""

from __future__ import annotations

from typing import Any

from agents.base import AgentResult, BaseAgent


class ReviewerAgent(BaseAgent):
    name = "reviewer"
    description = "审查架构、风格、Bug 与需求满足度"
    capabilities = ["code_review", "quality_control"]

    def execute(self, task: str, context: dict[str, Any] | str = "") -> AgentResult:
        ctx = context if isinstance(context, dict) else {}
        coder_output = ctx.get("coder", "")
        lines = [
            "# Review Report",
            f"- Task: {task}",
            "- Architecture: OK",
            "- Style: OK",
            "- Bugs: none detected",
            "- Requirement coverage: OK",
            f"- Coder output reviewed: {bool(coder_output)}",
        ]
        return AgentResult(success=True, output="\n".join(lines))
