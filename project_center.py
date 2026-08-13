"""Project center management."""

from __future__ import annotations

from pathlib import Path

from project_manager.manager import ProjectManager


def add_project(path: str | Path) -> dict:
    record = ProjectManager().register(path)
    return record.__dict__


def remove_project(path: str | Path) -> None:
    manager = ProjectManager()
    resolved = str(Path(path).resolve())
    manager.records.pop(resolved, None)
    manager._save()


def list_projects() -> list[dict]:
    return [item.__dict__ for item in ProjectManager().list()]


def switch_project(path: str | Path) -> dict:
    return ProjectManager().load(path)
