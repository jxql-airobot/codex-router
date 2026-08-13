"""Task assignment model."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TaskAssignment:
    name: str
    agent: str
    depends_on: list[str] = field(default_factory=list)
    status: str = "pending"
