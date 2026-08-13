"""Fast / complex path routing statistics for the dashboard."""

from __future__ import annotations

from typing import Any

from hooks.store import HookStore


def route_stats_report(store: HookStore | None = None) -> dict[str, Any]:
    """Return today's fast/complex routing counts, percentages and latencies."""
    store = store or HookStore()
    summary = store.route_summary()
    fast_count = summary["fast"]["count"]
    complex_count = summary["complex"]["count"]
    total = fast_count + complex_count
    return {
        "fast": {
            "count": fast_count,
            "percent": round(fast_count / total * 100, 1) if total else 0.0,
            "avg_latency_ms": summary["fast"]["avg_latency_ms"],
        },
        "complex": {
            "count": complex_count,
            "percent": round(complex_count / total * 100, 1) if total else 0.0,
            "avg_latency_ms": summary["complex"]["avg_latency_ms"],
        },
        "total": total,
    }


def format_report(report: dict[str, Any] | None = None) -> str:
    """Return a compact Chinese routing report matching the dashboard layout."""
    report = report or route_stats_report()
    fast = report["fast"]
    complex_ = report["complex"]
    return (
        f"今日任务: Fast {fast['percent']}% ({fast['count']}) "
        f"Complex {complex_['percent']}% ({complex_['count']})\n"
        f"平均响应: Fast {fast['avg_latency_ms'] / 1000:.1f}s "
        f"Complex {complex_['avg_latency_ms'] / 1000:.1f}s"
    )
