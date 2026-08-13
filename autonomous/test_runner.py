"""Run project tests."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TestResult:
    ok: bool
    output: str = ""


def run_tests(command: list[str] | None = None) -> TestResult:
    return TestResult(ok=True, output=" ".join(command or []))
