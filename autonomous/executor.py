"""Execute a single development step."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ExecutionResult:
    ok: bool
    output: str = ""


def execute_step(step: dict) -> ExecutionResult:
    return ExecutionResult(ok=True, output=step.get("name", ""))
