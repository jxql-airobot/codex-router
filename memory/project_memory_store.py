"""Persistent project long-term memory."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ProjectMemoryStore:
    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path or (Path(__file__).resolve().parents[1] / "data" / "project_memory.json"))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.data = self._load()

    def _load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"decisions": [], "failures": [], "experience": []}
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {"decisions": [], "failures": [], "experience": []}

    def _save(self) -> None:
        self.path.write_text(
            json.dumps(self.data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def add_decision(self, project: str, topic: str, choice: str, reason: str) -> dict:
        record = {"project": project, "topic": topic, "choice": choice, "reason": reason}
        self.data["decisions"].append(record)
        self._save()
        return record

    def add_failure(self, project: str, task: str, error: str, fix: str = "") -> dict:
        record = {"project": project, "task": task, "error": error, "fix": fix}
        self.data["failures"].append(record)
        self._save()
        return record

    def add_experience(self, project: str, context: str, lesson: str) -> dict:
        record = {"project": project, "context": context, "lesson": lesson}
        self.data["experience"].append(record)
        self._save()
        return record

    def decisions(self, project: str | None = None) -> list[dict]:
        return self._filter("decisions", project)

    def failures(self, project: str | None = None) -> list[dict]:
        return self._filter("failures", project)

    def experience(self, project: str | None = None) -> list[dict]:
        return self._filter("experience", project)

    def _filter(self, kind: str, project: str | None) -> list[dict]:
        records = self.data.get(kind, [])
        if project is None:
            return records
        return [record for record in records if record.get("project") == project]

    def query(self, project: str, question: str) -> list[dict]:
        text = question.lower()
        results: list[dict] = []
        for record in self.data["decisions"] + self.data["failures"] + self.data["experience"]:
            if record.get("project") != project:
                continue
            blob = json.dumps(record, ensure_ascii=False).lower()
            if any(word.lower() in blob for word in question.split() if word.strip()):
                results.append(record)
        return results
