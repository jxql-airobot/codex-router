"""Minimal task record used by the report generator."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TaskRecord:
    task: str = ""
    model: str = ""
    mode: str = ""
    changed_files: list[str] = field(default_factory=list)
    tests: str = ""
    commit: str = ""
    push: str = ""
    status: str = "pending"
