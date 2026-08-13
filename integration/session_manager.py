"""Track a complete AI development session."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SessionRecord:
    session_id: str
    input: str
    project: str = ""
    task_type: str = ""
    agents: list[str] = field(default_factory=list)
    models: list[str] = field(default_factory=list)
    tokens: int = 0
    result: str = "pending"

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "input": self.input,
            "project": self.project,
            "task_type": self.task_type,
            "agents": self.agents,
            "models": self.models,
            "tokens": self.tokens,
            "result": self.result,
        }


class SessionManager:
    def __init__(self) -> None:
        self._sessions: dict[str, SessionRecord] = {}

    def start(self, task: str, plan: dict[str, Any] | None = None) -> SessionRecord:
        session_id = uuid.uuid4().hex
        plan = plan or {}
        record = SessionRecord(
            session_id=session_id,
            input=task,
            project=plan.get("project", ""),
            task_type=plan.get("type", ""),
            agents=list(plan.get("recommended_agents", [])),
        )
        self._sessions[session_id] = record
        return record

    def finish(
        self,
        session_id: str,
        result: str,
        tokens: int = 0,
        models: list[str] | None = None,
    ) -> SessionRecord:
        record = self._sessions[session_id]
        record.result = result
        record.tokens = tokens
        if models:
            record.models = models
        return record

    def get(self, session_id: str) -> SessionRecord:
        return self._sessions[session_id]

    def snapshot(self) -> list[dict[str, Any]]:
        return [record.to_dict() for record in self._sessions.values()]
