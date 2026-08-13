"""Unified task classification result."""

from __future__ import annotations

from typing import Any

from classification.complexity import agents_for_score, score_complexity
from classification.intent import classify_intent


def classify_task(task: str, project_context: dict[str, Any] | None = None) -> dict[str, Any]:
    intent = classify_intent(task)
    complexity = score_complexity(task)
    project = (
        (project_context or {}).get("project_name")
        or (project_context or {}).get("project")
        or ""
    )
    return {
        "type": intent["type"],
        "domain": intent["domain"],
        "complexity": complexity,
        "recommended_workflow": intent["workflow"],
        "recommended_agents": agents_for_score(complexity),
        "project": project,
    }
