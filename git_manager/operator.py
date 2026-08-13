"""Perform safe git add / commit / push operations."""

from __future__ import annotations

import subprocess
from pathlib import Path

from git_manager.scanner import scan_git


def _run_git(root: Path, *args: str) -> tuple[int, str]:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode, (result.stdout + result.stderr).strip()


def stage_and_commit(root: str | Path, message: str) -> tuple[int, str]:
    info = scan_git(root)
    if not info.is_repo or info.root is None:
        return 1, "not a git repository"

    code, _ = _run_git(info.root, "add", "-A")
    if code != 0:
        return code, "git add failed"

    code, output = _run_git(info.root, "commit", "-m", message)
    if code != 0:
        return code, output or "git commit failed"
    return code, output


def push(root: str | Path, branch: str | None = None) -> tuple[int, str]:
    info = scan_git(root)
    if not info.is_repo or info.root is None:
        return 1, "not a git repository"
    if not info.remote:
        return 1, "no origin remote configured"

    target = branch or info.branch or "main"
    # Never use --force; push only the current branch.
    return _run_git(info.root, "push", "origin", target)
