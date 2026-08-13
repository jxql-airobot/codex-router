"""Analyze test errors."""

from __future__ import annotations


def analyze_error(output: str) -> dict:
    return {"has_error": bool(output), "summary": output[:200]}
