"""Data structures for usage records."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class UsageRecord:
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    project: str = ""
    task: str = ""
    agent: str = ""
    provider: str = ""
    model: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    cached_tokens: int = 0
    total_tokens: int = 0
    cost: float = 0.0
    task_id: str = ""
    commit_id: str = ""
    files_changed: int = 0
    tests_added: int = 0
    success: bool = False
    task_type: str = ""
    workflow: str = ""
