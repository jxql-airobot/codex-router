"""after_task hook: record task/session completion into usage SQLite.

Mapped to the official ``SessionEnd`` event. Advisory only — its output does
not keep the thread open.
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from hooks._common import (
    detect_project,
    extract,
    get_data_dir,
    read_stdin_json,
    safe_run,
)
from hooks.store import HookStore


def run() -> None:
    payload = read_stdin_json()
    info = extract(payload)
    cwd = info["cwd"]
    project = detect_project(cwd)

    try:
        from usage.database import UsageDatabase
        from usage.models import UsageRecord

        db = UsageDatabase(db_path=get_data_dir() / "usage.db")
        try:
            db.insert(
            UsageRecord(
                project=project,
                task=info["prompt"] or "",
                model=info["model"],
                task_id=info["session_id"],
                success=True,
            )
            )
        finally:
            db.close()
    except Exception:
        pass

    HookStore().record_session(
        info["session_id"],
        cwd,
        project,
        info["model"],
        "SessionEnd",
        info["reason"] or "other",
    )


if __name__ == "__main__":
    safe_run(run)
