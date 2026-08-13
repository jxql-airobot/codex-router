"""Dashboard launch helper."""

from __future__ import annotations

from pathlib import Path


def dashboard_path() -> Path:
    return Path(__file__).resolve().parents[1] / "dashboard" / "frontend" / "index.html"


def build_dashboard_command() -> str:
    return f'start "" "{dashboard_path()}"'
