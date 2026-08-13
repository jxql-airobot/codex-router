"""Text chart helpers used by the dashboard and CLI."""

from __future__ import annotations


def bar_chart(items: list[tuple[str, float]], width: int = 20) -> str:
    if not items:
        return ""
    maximum = max(value for _, value in items) or 1
    lines: list[str] = []
    for name, value in items:
        filled = int(round((value / maximum) * width))
        lines.append(f"{name:<12} {'█' * filled}")
    return "\n".join(lines)
