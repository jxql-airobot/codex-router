"""AI development efficiency metrics linked to git data."""

from __future__ import annotations

from typing import Any

from usage.tracker import UsageTracker


def efficiency(tracker: UsageTracker | None = None) -> dict[str, Any]:
    tracker = tracker or UsageTracker()
    rows = tracker.database.recent(1000)
    total_tokens = sum(row["total_tokens"] for row in rows)
    commits = {row.get("commit_id") for row in rows if row.get("commit_id")}
    files_changed = sum(int(row.get("files_changed") or 0) for row in rows)
    tests_added = sum(int(row.get("tests_added") or 0) for row in rows)
    tokens_per_commit = total_tokens / len(commits) if commits else 0
    return {
        "total_tokens": total_tokens,
        "commits": len(commits),
        "files_changed": files_changed,
        "tests_added": tests_added,
        "tokens_per_commit": tokens_per_commit,
    }
