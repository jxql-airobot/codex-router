"""Bounded, non-invasive project scanning for the memory layer."""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator


MARKER_FILES = ("README.md", "AGENTS.md", "PROJECT_STATUS.md", "ARCHITECTURE.md")

IGNORE_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "node_modules",
    "build",
    "install",
    "log",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    ".pytest_cache",
    ".idea",
    ".vscode",
    "dist",
}


@dataclass
class GitStatus:
    is_repo: bool = False
    branch: str | None = None
    dirty_files: list[str] = field(default_factory=list)
    recent_commits: list[str] = field(default_factory=list)


@dataclass
class ProjectScan:
    root: Path
    project_name: str
    markers: dict[str, Path | None]
    git: GitStatus
    tech_stack: list[str]
    file_count: int


def _run_git(root: Path, *args: str) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True,
            text=True,
            check=False,
        )
    except (FileNotFoundError, OSError):
        return ""
    return result.stdout if result.returncode == 0 else ""


def read_git_status(root: Path) -> GitStatus:
    if not (root / ".git").exists():
        return GitStatus()

    branch = _run_git(root, "rev-parse", "--abbrev-ref", "HEAD").strip()
    status_out = _run_git(root, "status", "--porcelain")
    dirty_files: list[str] = []
    for line in status_out.splitlines():
        if len(line) >= 3:
            dirty_files.append(line[3:])

    log_out = _run_git(root, "log", "-5", "--pretty=format:%s")
    recent_commits = [line for line in log_out.splitlines() if line.strip()]

    return GitStatus(
        is_repo=True,
        branch=branch or None,
        dirty_files=dirty_files,
        recent_commits=recent_commits,
    )


def detect_project_root(start: str | Path | None = None) -> Path:
    cwd = Path(start or os.getcwd()).expanduser().resolve()
    for candidate in (cwd, *cwd.parents):
        if (candidate / ".git").exists() or (candidate / "AGENTS.md").exists():
            return candidate
    return cwd


def _iter_files(root: Path, max_depth: int = 3, depth: int = 0) -> Iterator[Path]:
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
        yield entry


def _detect_stack(root: Path, max_depth: int = 3) -> tuple[list[str], int]:
    stack: set[str] = set()
    file_count = 0

    for path in _iter_files(root, max_depth=max_depth):
        file_count += 1
        name = path.name.lower()

        if name in {"requirements.txt", "pyproject.toml", "setup.py"} or path.suffix == ".py":
            stack.add("Python")
        if name == "package.xml" or name.endswith(".launch.py"):
            stack.add("ROS2")
        if name == "cmakelists.txt":
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")[:2000]
            except OSError:
                text = ""
            if "ament" in text or "catkin" in text or "ros2" in text.lower():
                stack.add("ROS2")
            else:
                stack.add("CMake")
        if path.suffix in {".world", ".sdf"} or "gazebo" in name:
            stack.add("Gazebo")
        if path.suffix in {".pt", ".onnx"} or "yolo" in name or "ultralytics" in name:
            stack.add("YOLO")
        if name == "package.json":
            stack.add("Node.js")
        if name in {"dockerfile", "docker-compose.yml", "docker-compose.yaml"}:
            stack.add("Docker")
        if path.suffix in {".urdf", ".xacro"}:
            stack.add("ROS2")

    return sorted(stack), file_count


def scan_project(start: str | Path | None = None) -> ProjectScan:
    root = detect_project_root(start)
    markers: dict[str, Path | None] = {}
    for name in MARKER_FILES:
        path = root / name
        markers[name] = path if path.exists() else None

    tech_stack, file_count = _detect_stack(root)
    git = read_git_status(root)
    return ProjectScan(
        root=root,
        project_name=root.name,
        markers=markers,
        git=git,
        tech_stack=tech_stack,
        file_count=file_count,
    )
