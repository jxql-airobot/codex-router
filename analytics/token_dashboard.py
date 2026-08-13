"""High-level token dashboard statistics."""

from __future__ import annotations

from typing import Any

from usage.tracker import UsageTracker


def overview(tracker: UsageTracker | None = None) -> dict[str, Any]:
    tracker = tracker or UsageTracker()
    data = tracker.database.total_since()
    return {
        "input_tokens": data["input_tokens"],
        "output_tokens": data["output_tokens"],
        "cached_tokens": data.get("cached_tokens", 0),
        "total_tokens": data["total_tokens"],
        "cost": data["cost"],
    }


def model_stats(tracker: UsageTracker | None = None) -> list[dict[str, Any]]:
    tracker = tracker or UsageTracker()
    return tracker.database.breakdown("model")


def project_stats(tracker: UsageTracker | None = None) -> list[dict[str, Any]]:
    tracker = tracker or UsageTracker()
    return tracker.database.breakdown("project")


def cache_stats(tracker: UsageTracker | None = None) -> dict[str, Any]:
    data = overview(tracker)
    total = data["total_tokens"] or 1
    return {
        "cached_tokens": data["cached_tokens"],
        "cache_hit_rate": data["cached_tokens"] / total,
        "saved_tokens": data["cached_tokens"],
    }
