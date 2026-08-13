"""Build a dependency graph from parsed files."""

from __future__ import annotations

from typing import Any


def build_graph(nodes: list[dict[str, Any]]) -> dict[str, Any]:
    edges: list[dict[str, str]] = []
    for node in nodes:
        source = node.get("path", "")
        for dep in set(node.get("imports", []) + node.get("calls", [])):
            if dep and dep != source:
                edges.append({"source": source, "target": dep, "type": "dependency"})
    return {"nodes": nodes, "edges": edges}
