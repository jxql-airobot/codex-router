"""Desktop AI status center entry point."""

from __future__ import annotations

from desktop.ai_status_window import render_status


def main() -> int:
    print(render_status())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
