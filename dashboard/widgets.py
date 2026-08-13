"""Dashboard widgets (text fallback when PySide6 is unavailable)."""

from __future__ import annotations

from usage.tracker import UsageTracker


def today_summary_widget() -> str:
    tracker = UsageTracker()
    today = tracker.database.total_since()
    tracker.close()
    return f"Today: {today['total_tokens']} tokens, ¥{today['cost']:.2f}"
