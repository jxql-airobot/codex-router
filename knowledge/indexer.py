"""Index project files and git history into a vector store."""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

from vector_store.store import VectorStore


MARKER_FILES = ("README.md", "AGENTS.md", "ARCHITECTURE.md", "PROJECT_STATUS.md")
CODE_EXTENSIONS = {
    ".py",
    ".md",
    ".yaml",
    ".yml",
    ".toml",
    ".json",
    ".sh",
    ".ps1",
    ".cmd",
    ".cpp",
    ".h",
    ".hpp",
    ".js",
    ".ts",
}
IGNORE_DIRS = {
    ".git",
    "node_modules",
    "build",
    "install",
    "log",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
}


@dataclass
class KnowledgeIndex:
    store: VectorStore
    source_files: int
    commit_chunks: int


def _chunk_text(text: str, max_chars: int = 1200) -> list[str]:
    text = text.strip()
    if len(text) <= max_chars:
        return [text] if text else []

    chunks: list[str] = []
    for i in range(0, len(text), max_chars):
        chunks.append(text[i : i + max_chars])
    return chunks


def _read_git_log(root: Path, limit: int = 30) -> list[str]:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "log", f"-{limit}", "--pretty=format:%h%x09%s%x09%b"],
            capture_output=True,
            text=True,
            check=False,
        )
    except (FileNotFoundError, OSError):
        return []
    if result.returncode != 0:
        return []
    return [line for line in result.stdout.splitlines() if line.strip()]


def _iter_files(root: Path, max_depth: int = 4, depth: int = 0):
    try:
        entries = list(root.iterdir())
    except OSError:
        return
    for entry in entries:
        if entry.name in IGNORE_DIRS:
            continue
        if entry.is_dir():
            if depth < max_depth:
                yield from _iter_files(entry, max_depth, depth + 1)
            continue
        if entry.suffix.lower() in CODE_EXTENSIONS:
            yield entry


def index_project(start: str | Path | None = None) -> KnowledgeIndex:
    root = Path(start or os.getcwd()).expanduser().resolve()
    store = VectorStore()
    source_files = 0

    for marker in MARKER_FILES:
        path = root / marker
        if not path.exists():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for index, chunk in enumerate(_chunk_text(text)):
            store.add(
                f"{marker}:{index}",
                chunk,
                {"source": marker, "type": "doc"},
            )
            source_files += 1

    for path in _iter_files(root):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        rel = str(path.relative_to(root))
        for index, chunk in enumerate(_chunk_text(text)):
            store.add(
                f"{rel}:{index}",
                chunk,
                {"source": rel, "type": "code"},
            )
            source_files += 1

    commit_chunks = 0
    for line in _read_git_log(root):
        store.add(
            f"commit:{line[:8]}",
            line,
            {"source": "git", "type": "commit"},
        )
        commit_chunks += 1

    return KnowledgeIndex(
        store=store,
        source_files=source_files,
        commit_chunks=commit_chunks,
    )
