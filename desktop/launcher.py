"""Desktop AI status center entry point."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from desktop.ai_status_window import render_status

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def main() -> int:
    print(render_status())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
