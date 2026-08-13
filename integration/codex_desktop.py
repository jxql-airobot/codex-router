"""Facade that mirrors the Codex Desktop flow."""

from __future__ import annotations

from typing import Any

from integration.interceptor import Interceptor
from integration.session_manager import SessionManager


class CodexDesktopIntegration:
    def __init__(self) -> None:
        self.interceptor = Interceptor(SessionManager())

    def run(self, task: str, project_context: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.interceptor.intercept(task, project_context)

    def complete(self, session_id: str, result: str, tokens: int = 0) -> dict[str, Any]:
        return self.interceptor.finish(session_id, result, tokens)
