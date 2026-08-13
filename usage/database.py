"""SQLite storage for usage records."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from usage.models import UsageRecord


class UsageDatabase:
    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = Path(db_path or (Path(__file__).resolve().parents[1] / "data" / "usage.db"))
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS usage_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                project TEXT,
                agent TEXT,
                provider TEXT,
                model TEXT,
                input_tokens INTEGER DEFAULT 0,
                output_tokens INTEGER DEFAULT 0,
                cached_tokens INTEGER DEFAULT 0,
                total_tokens INTEGER DEFAULT 0,
                cost REAL DEFAULT 0,
                task_id TEXT,
                task TEXT
            )
            """
        )
        self._conn.commit()

    def insert(self, record: UsageRecord) -> int:
        cursor = self._conn.execute(
            """
            INSERT INTO usage_records
            (timestamp, project, agent, provider, model, input_tokens,
             output_tokens, cached_tokens, total_tokens, cost, task_id, task)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.timestamp,
                record.project,
                record.agent,
                record.provider,
                record.model,
                record.input_tokens,
                record.output_tokens,
                record.cached_tokens,
                record.total_tokens,
                record.cost,
                record.task_id,
                record.task,
            ),
        )
        self._conn.commit()
        return int(cursor.lastrowid)

    def total_since(self, start: str | None = None) -> dict[str, Any]:
        if start is None:
            start = datetime.now(timezone.utc).date().isoformat()
        row = self._conn.execute(
            """
            SELECT COALESCE(SUM(total_tokens),0) AS total_tokens,
                   COALESCE(SUM(input_tokens),0) AS input_tokens,
                   COALESCE(SUM(output_tokens),0) AS output_tokens,
                   COALESCE(SUM(cost),0) AS cost
            FROM usage_records WHERE timestamp >= ?
            """,
            (start,),
        ).fetchone()
        return dict(row)

    def breakdown(self, column: str, start: str | None = None, limit: int = 10) -> list[dict[str, Any]]:
        if start is None:
            start = datetime.now(timezone.utc).date().isoformat()
        safe = column if column in {"provider", "model", "project", "agent"} else "provider"
        rows = self._conn.execute(
            f"""
            SELECT {safe} AS name, SUM(total_tokens) AS tokens, SUM(cost) AS cost
            FROM usage_records WHERE timestamp >= ?
            GROUP BY {safe} ORDER BY tokens DESC LIMIT ?
            """,
            (start, limit),
        ).fetchall()
        return [dict(row) for row in rows]

    def recent(self, limit: int = 10) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            """
            SELECT timestamp, project, agent, provider, model, total_tokens, cost
            FROM usage_records ORDER BY timestamp DESC LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]

    def close(self) -> None:
        self._conn.close()
