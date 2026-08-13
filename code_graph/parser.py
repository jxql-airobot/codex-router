"""Parse Python code into a lightweight symbol graph."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any


def parse_python(text: str, path: str = "") -> dict[str, Any]:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return {"path": path, "functions": [], "classes": [], "imports": [], "calls": []}

    functions: list[str] = []
    classes: list[str] = []
    imports: list[str] = []
    calls: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            functions.append(node.name)
        elif isinstance(node, ast.ClassDef):
            classes.append(node.name)
        elif isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                calls.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                calls.append(node.func.attr)

    return {
        "path": path,
        "functions": functions,
        "classes": classes,
        "imports": imports,
        "calls": calls,
    }


def parse_file(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    if path.suffix != ".py":
        return {"path": str(path), "functions": [], "classes": [], "imports": [], "calls": []}
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        text = ""
    return parse_python(text, str(path))
