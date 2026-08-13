"""In-memory recent task history for the integration layer."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SessionMemory:
    recent_tasks: list[str] = field(default_factory=list)

    def add(self, task: str) -> None:
        self.recent_tasks.append(task)

    def latest(self, limit: int = 10) -> list[str]:
        return self.recent_tasks[-limit:]
