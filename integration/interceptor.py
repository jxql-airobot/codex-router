"""Automatic interception and planning for a raw user task."""

from __future__ import annotations

from typing import Any

from classification.task_classifier import classify_task
from integration.session_manager import SessionManager


class Interceptor:
    def __init__(self, session_manager: SessionManager | None = None) -> None:
        self.sessions = session_manager or SessionManager()

    def intercept(self, task: str, project_context: dict[str, Any] | None = None) -> dict[str, Any]:
        plan = classify_task(task, project_context)
        session = self.sessions.start(task, plan)
        plan["session_id"] = session.session_id
        return plan

    def finish(self, session_id: str, result: str, tokens: int = 0) -> dict[str, Any]:
        record = self.sessions.finish(session_id, result, tokens)
        return record.to_dict()
