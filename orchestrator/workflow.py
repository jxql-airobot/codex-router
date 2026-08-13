"""Workflow configuration loading."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class Workflow:
    steps: list[str] = field(default_factory=list)
    retry_enabled: bool = False
    max_round: int = 3


def load_workflow(path: str | Path) -> Workflow:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    retry = data.get("retry", {})
    return Workflow(
        steps=list(data.get("workflow", [])),
        retry_enabled=bool(retry.get("enabled", False)),
        max_round=int(retry.get("max_round", 3)),
    )
