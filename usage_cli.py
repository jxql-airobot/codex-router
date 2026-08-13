"""CLI usage dashboard."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone

from usage.tracker import UsageTracker


def _fmt(value: float) -> str:
    if value >= 1_000_000_000:
        return f"{value / 1_000_000_000:.2f}B"
    if value >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"
    return f"{value:.0f}"


def render(detail: bool = False) -> str:
    tracker = UsageTracker()
    today = tracker.database.total_since(datetime.now(timezone.utc).date().isoformat())
    lines = [
        "Today Usage",
        f"Tokens: {_fmt(today['total_tokens'])}",
        f"Cost: ¥{today['cost']:.2f}",
        f"Input: {_fmt(today['input_tokens'])}",
        f"Output: {_fmt(today['output_tokens'])}",
    ]
    project = tracker.database.breakdown("project", limit=1)
    if project:
        lines.append(f"Top Project: {project[0]['name']}")

    if detail:
        lines.append("\nModel Usage")
        for row in tracker.database.breakdown("model"):
            lines.append(f"{row['name']}: {_fmt(row['tokens'])}")
        lines.append("\nProject Usage")
        for row in tracker.database.breakdown("project"):
            lines.append(f"{row['name']}: {_fmt(row['tokens'])}")
        lines.append("\nAgent Usage")
        for row in tracker.database.breakdown("agent"):
            lines.append(f"{row['name']}: {_fmt(row['tokens'])}")

    tracker.close()
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Token usage dashboard")
    parser.add_argument("--detail", action="store_true")
    args = parser.parse_args(argv)
    print(render(detail=args.detail))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
