"""Record failure experience."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class FailureRecord:
    task: str
    error: str
    fix: str = ""
