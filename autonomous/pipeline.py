"""Autonomous development loop."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from autonomous.error_analyzer import analyze_error
from autonomous.repair_agent import repair_plan


@dataclass
class PipelineResult:
    ok: bool
    attempts: int = 0
    report: str = ""
    history: list[dict[str, Any]] = field(default_factory=list)


def run_pipeline(
    task: str,
    executor: Callable[[], Any],
    tester: Callable[[], Any],
    max_retry: int = 5,
) -> PipelineResult:
    attempts = 0
    for attempt in range(max_retry):
        attempts += 1
        execution = executor()
        test = tester()
        history = {
            "attempt": attempts,
            "test_ok": test.ok,
            "output": getattr(test, "output", ""),
        }
        if test.ok:
            return PipelineResult(
                ok=True,
                attempts=attempts,
                report=f"success after {attempts} attempts",
                history=[history],
            )
        error = analyze_error(getattr(test, "output", ""))
        repairs = repair_plan(error)
        history["repairs"] = repairs
    return PipelineResult(
        ok=False,
        attempts=attempts,
        report=f"failed after {attempts} attempts",
        history=[history],
    )
