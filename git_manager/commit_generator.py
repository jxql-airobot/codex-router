"""Generate a conventional commit message from a diff summary."""

from __future__ import annotations

from pathlib import Path

from git_manager.diff_analyzer import DiffSummary


COMMIT_TYPES = ("feat", "fix", "refactor", "docs", "test")


def _all_match(paths: list[str], predicate) -> bool:
    return bool(paths) and all(predicate(p) for p in paths)


def _infer_type(diff: DiffSummary) -> str:
    all_paths = (
        diff.added + diff.modified + diff.deleted + diff.untracked
    )
    if _all_match(all_paths, lambda p: p.lower().endswith(".md")):
        return "docs"
    if _all_match(all_paths, lambda p: "test" in Path(p).name.lower() or "/tests/" in p.replace("\\", "/")):
        return "test"
    if diff.deleted and not (diff.added or diff.modified):
        return "refactor"
    if diff.added or diff.untracked:
        return "feat"
    return "fix"


def _subject(diff: DiffSummary) -> str:
    paths = (diff.added + diff.modified + diff.deleted + diff.untracked)[:3]
    if not paths:
        return "update repository"
    return ", ".join(paths)


def generate_commit_message(
    diff: DiffSummary,
    explicit_type: str | None = None,
) -> str:
    if explicit_type:
        commit_type = explicit_type.strip().rstrip(":").lower()
        if commit_type not in COMMIT_TYPES:
            commit_type = "feat"
    else:
        commit_type = _infer_type(diff)
    return f"{commit_type}: {_subject(diff)}"
