"""SQLite persistence for hook events (classifications, errors, sessions).

Each operation opens a short-lived connection so hook processes never leave a
file handle open (important on Windows, where open handles block file moves).
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from hooks._common import get_data_dir


class HookStore:
    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = Path(db_path or (get_data_dir() / "hook_events.db"))
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        conn = self._connect()
        try:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS classifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    session_id TEXT,
                    cwd TEXT,
                    project TEXT,
                    prompt TEXT,
                    task_type TEXT,
                    domain TEXT,
                    complexity INTEGER,
                    recommended_workflow TEXT,
                    recommended_agents TEXT,
                    recommended_model TEXT,
                    planning_level INTEGER
                );
                CREATE TABLE IF NOT EXISTS errors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    session_id TEXT,
                    cwd TEXT,
                    project TEXT,
                    event TEXT,
                    detail TEXT
                );
                CREATE TABLE IF NOT EXISTS session_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    session_id TEXT,
                    cwd TEXT,
                    project TEXT,
                    model TEXT,
                    event TEXT,
                    reason TEXT,
                    payload TEXT
                );
                CREATE TABLE IF NOT EXISTS tool_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    session_id TEXT,
                    cwd TEXT,
                    project TEXT,
                    tool_name TEXT,
                    task TEXT,
                    result_summary TEXT,
                    model TEXT,
                    provider TEXT,
                    input_tokens INTEGER DEFAULT 0,
                    output_tokens INTEGER DEFAULT 0,
                    total_tokens INTEGER DEFAULT 0,
                    git_status TEXT,
                    duration_ms INTEGER DEFAULT 0,
                    success INTEGER DEFAULT 1
                );
                CREATE TABLE IF NOT EXISTS session_summaries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    session_id TEXT,
                    cwd TEXT,
                    project TEXT,
                    model TEXT,
                    summary TEXT,
                    error_count INTEGER DEFAULT 0,
                    tool_count INTEGER DEFAULT 0,
                    recent_tasks TEXT
                );
                """
            )
            conn.commit()
        finally:
            conn.close()

    def record_classification(
        self,
        session_id: str,
        cwd: str,
        project: str,
        prompt: str,
        result: dict[str, Any],
    ) -> None:
        conn = self._connect()
        try:
            conn.execute(
                """
                INSERT INTO classifications
                (timestamp, session_id, cwd, project, prompt, task_type, domain,
                 complexity, recommended_workflow, recommended_agents,
                 recommended_model, planning_level)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    datetime.now(timezone.utc).isoformat(),
                    session_id,
                    cwd,
                    project,
                    prompt,
                    result.get("type", ""),
                    result.get("domain", ""),
                    int(result.get("complexity", 0)),
                    result.get("recommended_workflow", ""),
                    ",".join(result.get("recommended_agents", [])),
                    result.get("recommended_model", ""),
                    int(result.get("planning_level", 0)),
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def record_error(
        self,
        session_id: str,
        cwd: str,
        project: str,
        event: str,
        detail: str,
    ) -> None:
        conn = self._connect()
        try:
            conn.execute(
                """
                INSERT INTO errors (timestamp, session_id, cwd, project, event, detail)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    datetime.now(timezone.utc).isoformat(),
                    session_id,
                    cwd,
                    project,
                    event,
                    str(detail),
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def record_session(
        self,
        session_id: str,
        cwd: str,
        project: str,
        model: str,
        event: str,
        reason: str = "",
        payload: dict[str, Any] | None = None,
    ) -> None:
        conn = self._connect()
        try:
            conn.execute(
                """
                INSERT INTO session_events
                (timestamp, session_id, cwd, project, model, event, reason, payload)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    datetime.now(timezone.utc).isoformat(),
                    session_id,
                    cwd,
                    project,
                    model,
                    event,
                    reason,
                    json.dumps(payload or {}, ensure_ascii=False),
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def record_tool_event(
        self,
        session_id: str,
        cwd: str,
        project: str,
        tool_name: str,
        task: str = "",
        result_summary: str = "",
        model: str = "",
        provider: str = "",
        input_tokens: int = 0,
        output_tokens: int = 0,
        total_tokens: int = 0,
        git_status: str = "",
        duration_ms: int = 0,
        success: bool = True,
    ) -> None:
        conn = self._connect()
        try:
            conn.execute(
                """
                INSERT INTO tool_events
                (timestamp, session_id, cwd, project, tool_name, task,
                 result_summary, model, provider, input_tokens, output_tokens,
                 total_tokens, git_status, duration_ms, success)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    datetime.now(timezone.utc).isoformat(),
                    session_id,
                    cwd,
                    project,
                    tool_name,
                    task,
                    result_summary,
                    model,
                    provider,
                    int(input_tokens),
                    int(output_tokens),
                    int(total_tokens),
                    git_status,
                    int(duration_ms),
                    int(success),
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def record_session_summary(
        self,
        session_id: str,
        cwd: str,
        project: str,
        model: str,
        summary: str,
        error_count: int = 0,
        tool_count: int = 0,
        recent_tasks: list[str] | None = None,
    ) -> None:
        conn = self._connect()
        try:
            conn.execute(
                """
                INSERT INTO session_summaries
                (timestamp, session_id, cwd, project, model, summary,
                 error_count, tool_count, recent_tasks)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    datetime.now(timezone.utc).isoformat(),
                    session_id,
                    cwd,
                    project,
                    model,
                    summary,
                    int(error_count),
                    int(tool_count),
                    json.dumps(recent_tasks or [], ensure_ascii=False),
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def latest_task(self, session_id: str) -> str:
        """Return the most recently classified prompt for a session."""
        conn = self._connect()
        try:
            row = conn.execute(
                """
                SELECT prompt FROM classifications
                WHERE session_id = ? AND prompt IS NOT NULL AND prompt != ''
                ORDER BY id DESC LIMIT 1
                """,
                (session_id,),
            ).fetchone()
            return str(row[0]) if row else ""
        finally:
            conn.close()

    def session_stats(self, session_id: str) -> dict[str, Any]:
        """Return tool/error counts and recent tasks for a session."""
        conn = self._connect()
        try:
            tool_count = conn.execute(
                "SELECT COUNT(*) FROM tool_events WHERE session_id = ?",
                (session_id,),
            ).fetchone()[0]
            error_count = conn.execute(
                "SELECT COUNT(*) FROM errors WHERE session_id = ?",
                (session_id,),
            ).fetchone()[0]
            rows = conn.execute(
                """
                SELECT prompt FROM classifications
                WHERE session_id = ? AND prompt IS NOT NULL AND prompt != ''
                ORDER BY id DESC LIMIT 5
                """,
                (session_id,),
            ).fetchall()
        finally:
            conn.close()
        return {
            "tool_count": int(tool_count),
            "error_count": int(error_count),
            "recent_tasks": [str(row[0]) for row in rows],
        }

    def list_tables(self) -> set[str]:
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            return {row[0] for row in rows}
        finally:
            conn.close()

    def count(self, table: str) -> int:
        conn = self._connect()
        try:
            row = conn.execute(f"SELECT COUNT(*) AS n FROM {table}").fetchone()
            return int(row["n"]) if row else 0
        finally:
            conn.close()
