"""Generate repair plans."""

from __future__ import annotations


def repair_plan(error: dict) -> list[str]:
    return ["fix"] if error.get("has_error") else []
