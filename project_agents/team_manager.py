"""Project team management."""

from __future__ import annotations


def load_team(project: str, config: dict | None = None) -> list[str]:
    return (config or {}).get(project, [])
