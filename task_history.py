"""Persistent task history."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from typing import Any


class TaskHistoryStore:
    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = Path(db_path or (Path(__file__).resolve().parent / "data" / "task_history.db"))
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self._init()

    def _init(self) -> None:
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS task_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                time TEXT,
                project TEXT,
                task TEXT,
                model TEXT,
                agent TEXT,
                tokens INTEGER,
                result TEXT,
                duration_seconds REAL
            )
            """
        )
        self.conn.commit()

    def add(
        self,
        project: str,
        task: str,
        model: str = "",
        agent: str = "",
        tokens: int = 0,
        result: str = "success",
        duration_seconds: float = 0.0,
    ) -> int:
        cursor = self.conn.execute(
            """
            INSERT INTO task_history
            (time, project, task, model, agent, tokens, result, duration_seconds)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now(timezone.utc).isoformat(),
                project,
                task,
                model,
                agent,
                tokens,
                result,
                duration_seconds,
            ),
        )
        self.conn.commit()
        return int(cursor.lastrowid)

    def list(self, limit: int = 20) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM task_history ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]

    def close(self) -> None:
        self.conn.close()
