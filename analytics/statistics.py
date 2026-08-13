"""Chinese-formatted usage statistics."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from usage.tracker import UsageTracker


def format_number(value: float) -> str:
    if value >= 1_000_000_000:
        return f"{value / 1_000_000_000:.1f}B"
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"{value / 1_000:.1f}K"
    return f"{value:.0f}"


def chinese_number(value: float) -> str:
    if value >= 100_000_000:
        return f"{value / 100_000_000:.1f}亿"
    if value >= 10_000:
        return f"{value / 10_000:.1f}万"
    return f"{value:.0f}"


def overview(tracker: UsageTracker | None = None) -> dict[str, Any]:
    tracker = tracker or UsageTracker()
    today = tracker.database.total_since(datetime.now(timezone.utc).date().isoformat())
    cache_hit = 0.0
    if today["total_tokens"]:
        cache_hit = tracker.database.total_since(datetime.now(timezone.utc).date().isoformat())["output_tokens"]
    return {
        "total_tokens": today["total_tokens"],
        "input_tokens": today["input_tokens"],
        "output_tokens": today["output_tokens"],
        "cached_tokens": today.get("cached_tokens", 0),
        "cache_hit_rate": cache_hit,
        "cost": today["cost"],
        "total_display": chinese_number(today["total_tokens"]),
    }


def breakdowns(tracker: UsageTracker | None = None) -> dict[str, list[dict[str, Any]]]:
    tracker = tracker or UsageTracker()
    return {
        "projects": tracker.database.breakdown("project"),
        "models": tracker.database.breakdown("model"),
        "agents": tracker.database.breakdown("agent"),
    }


def token_history(tracker: UsageTracker | None = None) -> list[dict[str, Any]]:
    tracker = tracker or UsageTracker()
    rows = tracker.database.recent(100)
    return [
        {"date": row["timestamp"][:10], "tokens": row["total_tokens"]}
        for row in rows
    ]
