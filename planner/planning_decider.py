"""Decide the planning level for a task."""

from __future__ import annotations

from typing import Any

from classification.complexity import score_complexity
from planner.planning_level import AGENTS_BY_LEVEL, MODE_BY_LEVEL, WORKFLOW_BY_LEVEL
from planner.task_analyzer import analyze_task
from planner.task_intent import classify_intent


def decide(task: str) -> dict[str, Any]:
    features = analyze_task(task)
    intent = classify_intent(features)
    complexity = score_complexity(task)

    if intent == "explicit":
        level = 0
        reason = "用户已经提供完整执行计划"
        confidence = 0.95
    elif intent == "semi":
        level = 1
        reason = "用户提供多个任务，但需要整理依赖"
        confidence = 0.85
    else:
        level = 2
        reason = "目标模糊，需要架构设计与完整规划"
        confidence = 0.7 if complexity < 7 else 0.9

    return {
        "planning_level": level,
        "mode": MODE_BY_LEVEL[level],
        "workflow": WORKFLOW_BY_LEVEL[level],
        "agents": AGENTS_BY_LEVEL[level],
        "complexity": complexity,
        "confidence": confidence,
        "reason": reason,
        "features": features,
    }
