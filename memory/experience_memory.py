"""Record engineering experience."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ExperienceRecord:
    context: str
    lesson: str
