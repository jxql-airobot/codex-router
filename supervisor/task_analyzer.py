"""Analyze a task for supervisor orchestration."""

from __future__ import annotations

from typing import Any

from classification.task_classifier import classify_task
from planner.planning_decider import decide


def analyze_task(task: str, project: str = "") -> dict[str, Any]:
    classified = classify_task(task)
    planning = decide(task)
    return {
        "type": classified["type"],
        "domain": classified["domain"],
        "difficulty": classified["complexity"],
        "planning_level": planning["planning_level"],
        "mode": planning["mode"],
        "project": project or classified["project"],
    }
