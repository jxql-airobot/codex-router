"""Windows notification helper (non-blocking placeholder)."""

from __future__ import annotations


def notify(title: str, message: str) -> str:
    # Kept as a local hook; real toast can be added later without changing callers.
    return f"[通知] {title}: {message}"
