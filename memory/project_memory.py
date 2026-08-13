"""Project-level long-term memory."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ProjectMemory:
    project: str
    decisions: list[str] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)
    experience: list[str] = field(default_factory=list)
