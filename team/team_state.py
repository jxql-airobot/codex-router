"""Team and agent state."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class AgentState:
    agent: str
    status: str = "idle"
    current_task: str = ""
    progress: int = 0

    def to_dict(self) -> dict:
        return {
            "agent": self.agent,
            "status": self.status,
            "current_task": self.current_task,
            "progress": self.progress,
        }
