"""Automatic task classification statistics."""

from __future__ import annotations

from typing import Any

from usage.tracker import UsageTracker


def classification_stats(tracker: UsageTracker | None = None) -> list[dict[str, Any]]:
    tracker = tracker or UsageTracker()
    rows = tracker.database.recent(10000)
    buckets: dict[str, int] = {}
    for row in rows:
        task_type = row.get("task_type") or "unknown"
        buckets[task_type] = buckets.get(task_type, 0) + 1
    total = sum(buckets.values()) or 1
    return [
        {"type": task_type, "count": count, "ratio": count / total}
        for task_type, count in sorted(buckets.items(), key=lambda item: item[1], reverse=True)
    ]
