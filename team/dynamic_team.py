"""Dynamic team model."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DynamicTeam:
    project: str
    members: list[dict] = field(default_factory=list)
