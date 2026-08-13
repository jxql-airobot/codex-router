"""Commit completed work without pushing."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from git_manager.commit_generator import generate_commit_message
from git_manager.diff_analyzer import analyze_diff
from git_manager.operator import stage_and_commit


@dataclass
class GitResult:
    ok: bool
    message: str = ""


def commit_work(repo: str | Path | None = None, commit: bool = True) -> GitResult:
    diff = analyze_diff(repo)
    message = generate_commit_message(diff)
    if not commit:
        return GitResult(ok=True, message=message)
    if diff.is_empty:
        return GitResult(ok=True, message="no changes")
    code, output = stage_and_commit(repo or ".", message)
    return GitResult(ok=code == 0, message=message or output)
