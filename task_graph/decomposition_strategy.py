"""Decide the decomposition level for a task."""

from __future__ import annotations

from typing import Any

from task_graph.task_complexity import (
    detect_domains,
    file_count,
    has_dependency_words,
    has_user_steps,
    is_forbidden,
    is_must_decompose,
)


def decide(task: str) -> dict[str, Any]:
    domains = detect_domains(task)
    files = file_count(task)

    if is_forbidden(task):
        return {
            "decomposition_level": 0,
            "need_subtask": False,
            "reason": "明确修改，无需拆解",
            "estimated_agents": 1,
        }

    if has_user_steps(task) and not is_must_decompose(task):
        return {
            "decomposition_level": 0,
            "need_subtask": False,
            "reason": "用户已提供完整步骤，不重复拆解",
            "estimated_agents": 1,
        }

    if is_must_decompose(task) or len(domains) >= 2:
        agents = max(2, min(len(domains) + 2, 8))
        return {
            "decomposition_level": 2,
            "need_subtask": True,
            "reason": "涉及多领域或多模块，需要完整 Task Graph",
            "estimated_agents": agents,
        }

    if len(domains) == 1:
        return {
            "decomposition_level": 1,
            "need_subtask": True,
            "reason": "单 Agent 多步骤，需要轻量拆解",
            "estimated_agents": 1,
        }

    if files <= 2 and not has_dependency_words(task):
        return {
            "decomposition_level": 0,
            "need_subtask": False,
            "reason": "简单明确任务，直接执行",
            "estimated_agents": 1,
        }

    return {
        "decomposition_level": 1,
        "need_subtask": True,
        "reason": "单 Agent 多步骤，需要轻量拆解",
        "estimated_agents": 1,
    }
