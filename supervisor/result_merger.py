"""Merge team outputs."""

from __future__ import annotations

from typing import Any


def merge_results(outputs: dict[str, Any]) -> str:
    lines = ["# Supervisor Result"]
    for agent, output in outputs.items():
        lines.append(f"\n## {agent}\n{output}")
    return "\n".join(lines)
