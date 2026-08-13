"""Daily activity heatmap generation."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from typing import Any

from usage.tracker import UsageTracker


def daily_activity(tracker: UsageTracker | None = None, days: int = 365) -> list[dict[str, Any]]:
    tracker = tracker or UsageTracker()
    rows = tracker.database.recent(10000)
    buckets: dict[str, int] = defaultdict(int)
    for row in rows:
        day = row["timestamp"][:10]
        buckets[day] += int(row["total_tokens"])

    today = date.today()
    return [
        {
            "date": (today - timedelta(days=offset)).isoformat(),
            "tokens": buckets.get((today - timedelta(days=offset)).isoformat(), 0),
        }
        for offset in range(days)
    ]
