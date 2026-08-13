"""Record design decisions."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DecisionRecord:
    topic: str
    choice: str
    reason: str
