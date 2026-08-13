"""session_end hook: persist a session summary and project memory at exit.

Mapped to the official ``SessionEnd`` event. It aggregates tool activity and
errors for the session, writes a summary into SQLite, and stores a lightweight
project experience record. It is advisory only and always fails open.
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
    log_hook,
    read_stdin_json,
    safe_run,
    summarize,
)
from hooks.store import HookStore


def run() -> None:
    payload = read_stdin_json()
    info = extract(payload)
    session_id = info["session_id"]
    cwd = info["cwd"]
    project = detect_project(cwd)

    store = HookStore()
    stats = store.session_stats(session_id)
    recent_tasks = stats.get("recent_tasks") or []

    summary_parts = [
        f"session={session_id}",
        f"project={project or '-'}",
        f"model={info['model']}",
        f"reason={info['reason'] or 'other'}",
        f"tool_events={stats.get('tool_count', 0)}",
        f"errors={stats.get('error_count', 0)}",
    ]
    if recent_tasks:
        summary_parts.append("recent_tasks=" + " | ".join(recent_tasks[:5]))
    summary = summarize("; ".join(summary_parts), limit=2000)

    store.record_session_summary(
        session_id=session_id,
        cwd=cwd,
        project=project,
        model=info["model"],
        summary=summary,
        error_count=stats.get("error_count", 0),
        tool_count=stats.get("tool_count", 0),
        recent_tasks=recent_tasks,
    )
    store.record_session(
        session_id,
        cwd,
        project,
        info["model"],
        "SessionEnd",
        info["reason"] or "other",
    )

    try:
        from memory.project_memory_store import ProjectMemoryStore

        ProjectMemoryStore(path=get_data_dir() / "project_memory.json").add_experience(
            project or "general",
            f"session {session_id}",
            summary[:500],
        )
    except Exception:
        pass

    log_hook(f"SessionEnd session={session_id} project={project} summary={summary[:200]}")


if __name__ == "__main__":
    safe_run(run)
