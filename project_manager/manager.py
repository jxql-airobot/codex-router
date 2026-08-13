"""Project registry: identify, load memory/RAG, and keep history."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from knowledge.indexer import index_project
from memory.context_builder import build_context


@dataclass
class ProjectRecord:
    name: str
    path: str
    tech_stack: list[str] = field(default_factory=list)
    domain: str = ""
    history: list[str] = field(default_factory=list)


class ProjectManager:
    def __init__(self, registry_path: str | Path | None = None) -> None:
        self.registry_path = Path(
            registry_path or (Path.home() / ".codex" / "projects.json")
        )
        self.records: dict[str, dict[str, Any]] = self._load()

    def _load(self) -> dict[str, dict[str, Any]]:
        if not self.registry_path.exists():
            return {}
        try:
            return json.loads(self.registry_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}

    def _save(self) -> None:
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        self.registry_path.write_text(
            json.dumps(self.records, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def register(self, path: str | Path, domain: str = "") -> ProjectRecord:
        resolved = Path(path).expanduser().resolve()
        context = build_context(resolved)
        from launcher.dynamic_planner import detect_domain

        record = ProjectRecord(
            name=context.project_name,
            path=str(resolved),
            tech_stack=context.tech_stack,
            domain=domain or detect_domain(context.project_name),
        )
        self.records[str(resolved)] = asdict(record)
        self._save()
        return record

    def list(self) -> list[ProjectRecord]:
        return [ProjectRecord(**item) for item in self.records.values()]

    def load(self, path: str | Path) -> dict[str, Any]:
        resolved = Path(path).expanduser().resolve()
        context = build_context(resolved)
        index = index_project(resolved)
        return {
            "project": context.project_name,
            "tech_stack": context.tech_stack,
            "memory": context,
            "rag": index,
        }

    def save_history(self, path: str | Path, entry: str) -> None:
        resolved = Path(path).expanduser().resolve()
        key = str(resolved)
        if key not in self.records:
            self.register(resolved)
        history = self.records[key].setdefault("history", [])
        history.append(entry)
        self._save()
