"""Index Python files in a project."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from code_graph.dependency_graph import build_graph
from code_graph.parser import parse_file


def index_project(root: str | Path) -> dict[str, Any]:
    root = Path(root)
    nodes = []
    for path in root.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        nodes.append(parse_file(path))
    graph = build_graph(nodes)
    return {"root": str(root), "files": nodes, "graph": graph}
