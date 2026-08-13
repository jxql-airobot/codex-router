"""0-10 complexity score and agent selection."""

from __future__ import annotations

from classifier import classify


def score_complexity(task: str) -> int:
    raw = classify(task).score
    return max(0, min(10, round(raw / 10)))


def agents_for_score(score: int) -> list[str]:
    if score <= 3:
        return ["coder"]
    if score <= 7:
        return ["planner", "coder"]
    return ["planner", "coder", "tester", "reviewer"]
