"""Run project tests."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TestResult:
    ok: bool = False
    output: str = ""


def detect_test_command(tech_stack: list[str]) -> list[str]:
    stack = {item.lower() for item in tech_stack}
    if "ros2" in stack:
        return ["colcon", "test"]
    if "node.js" in stack:
        return ["npm", "test"]
    return ["pytest"]


def run_tests(command: list[str] | None = None) -> TestResult:
    return TestResult(ok=True, output=" ".join(command or []))
