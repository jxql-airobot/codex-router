"""Automatic provider fallback and task recovery."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TaskState:
    task_id: str
    current_stage: str
    completed_steps: list[str] = field(default_factory=list)
    failed_provider: str = ""
    next_provider: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "current_stage": self.current_stage,
            "completed_steps": self.completed_steps,
            "failed_provider": self.failed_provider,
            "next_provider": self.next_provider,
        }


class FallbackManager:
    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config

    def chain(self, role: str) -> list[str]:
        return list(self.config.get("fallback", {}).get(role, []))

    def select(self, role: str, failed_provider: str | None = None) -> str | None:
        chain = self.chain(role)
        if failed_provider is None:
            routing = self.config.get("role_routing", {}).get(role, {})
            return routing.get("provider") or (chain[0] if chain else None)
        for provider in chain:
            if provider != failed_provider:
                return provider
        return None

    def recover(self, task_id: str, current_stage: str, completed_steps: list[str], failed_provider: str) -> TaskState:
        role = current_stage
        next_provider = self.select(role, failed_provider)
        return TaskState(
            task_id=task_id,
            current_stage=current_stage,
            completed_steps=completed_steps,
            failed_provider=failed_provider,
            next_provider=next_provider or "",
        )
