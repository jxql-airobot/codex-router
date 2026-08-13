"""Tester agent detects and runs the appropriate test command."""

from __future__ import annotations

import subprocess
from typing import Any

from agents.base import AgentResult, BaseAgent


class TesterAgent(BaseAgent):
    name = "tester"
    description = "发现并执行项目测试"
    capabilities = ["testing", "verification"]

    def _detect_command(self, context: dict[str, Any]) -> list[str]:
        stack = {item.lower() for item in context.get("tech_stack", [])}
        if "ros2" in stack:
            return ["colcon", "test"]
        if "node.js" in stack:
            return ["npm", "test"]
        return ["pytest"]

    def execute(self, task: str, context: dict[str, Any] | str = "") -> AgentResult:
        ctx = context if isinstance(context, dict) else {}
        command = self._detect_command(ctx)
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
                timeout=120,
            )
        except (OSError, subprocess.TimeoutExpired):
            return AgentResult(success=False, output=f"test command failed: {command}")
        success = result.returncode == 0
        output = (result.stdout or result.stderr).strip() or "no test output"
        return AgentResult(
            success=success,
            output=output,
            metadata={"command": " ".join(command), "returncode": result.returncode},
        )
