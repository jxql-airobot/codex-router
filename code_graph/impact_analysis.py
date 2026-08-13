"""Analyze impact of a symbol."""

from __future__ import annotations

from typing import Any


def analyze_impact(symbol: str, graph: dict[str, Any]) -> list[str]:
    impacted: set[str] = set()
    for edge in graph.get("edges", []):
        if symbol in (edge.get("source"), edge.get("target")):
            impacted.add(edge["source"])
            impacted.add(edge["target"])
    return sorted(impacted)
