"""Read-only Git repository scanning."""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class GitInfo:
    is_repo: bool = False
    root: Path | None = None
    branch: str | None = None
    remote: str | None = None
    modified_files: list[str] = field(default_factory=list)
    recent_commits: list[str] = field(default_factory=list)


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


def find_repo_root(start: str | Path | None = None) -> Path | None:
    cwd = Path(start or os.getcwd()).expanduser().resolve()
    for candidate in (cwd, *cwd.parents):
        if (candidate / ".git").exists():
            return candidate
    return None


def scan_git(start: str | Path | None = None) -> GitInfo:
    root = find_repo_root(start)
    if root is None:
        return GitInfo()

    branch = _run_git(root, "rev-parse", "--abbrev-ref", "HEAD").strip()
    remote = _run_git(root, "remote", "get-url", "origin").strip()

    status = _run_git(root, "status", "--porcelain")
    modified_files = [line[3:] for line in status.splitlines() if len(line) >= 3]

    log = _run_git(root, "log", "-5", "--pretty=format:%s")
    recent_commits = [line for line in log.splitlines() if line.strip()]

    return GitInfo(
        is_repo=True,
        root=root,
        branch=branch or None,
        remote=remote or None,
        modified_files=modified_files,
        recent_commits=recent_commits,
    )
