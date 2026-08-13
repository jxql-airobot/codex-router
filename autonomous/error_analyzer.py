"""Analyze test errors."""

from __future__ import annotations


def analyze_error(output: str) -> dict:
    text = output.strip()
    return {"has_error": bool(text), "summary": text[:200]}
