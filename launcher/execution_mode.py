"""Execution-mode routing for the Codex model router.

The router no longer only picks a model; it also picks how to execute a task:

- ``direct``: one Flash/Pro codex call, no planning or agents.
- ``enhanced``: print a lightweight plan and risk block, then one codex call.
- ``agent``: run a supervised multi-role pipeline (Planner -> Coder -> Tester
  -> Reviewer).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AgentRole:
    name: str
    model_tier: str
    sandbox: str = "read-only"


ROLE_ORDER = ("planner", "coder", "tester", "reviewer")


def determine_execution_mode(
    score: int,
    config: dict[str, Any],
    override: str | None = None,
) -> str:
    """Return one of ``direct``, ``enhanced``, or ``agent``."""
    if override in {"direct", "enhanced", "agent"}:
        return override

    thresholds = config.get("execution", {})
    direct_threshold = int(thresholds.get("direct_threshold", 40))
    enhanced_threshold = int(thresholds.get("enhanced_threshold", 70))

    if score < direct_threshold:
        return "direct"
    if score < enhanced_threshold:
        return "enhanced"
    return "agent"


def load_roles(config: dict[str, Any]) -> list[AgentRole]:
    roles_cfg = config.get("agent_roles", {})
    roles: list[AgentRole] = []
    for name in ROLE_ORDER:
        cfg = roles_cfg.get(name, {})
        model_tier = cfg.get("model", "flash")
        sandbox = cfg.get("sandbox", "read-only")
        roles.append(AgentRole(name=name, model_tier=model_tier, sandbox=sandbox))
    return roles


def model_display_name(tier: str, config: dict[str, Any]) -> str:
    model_cfg = config.get("models", {}).get(tier, {})
    if isinstance(model_cfg, dict):
        return model_cfg.get("model_name") or model_cfg.get("model") or tier
    return tier
