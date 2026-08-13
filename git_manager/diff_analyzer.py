"""Classify working-tree changes into added / modified / deleted."""

from __future__ import annotations

from dataclasses import dataclass, field

from git_manager.scanner import scan_git


@dataclass
class DiffSummary:
    added: list[str] = field(default_factory=list)
    modified: list[str] = field(default_factory=list)
    deleted: list[str] = field(default_factory=list)
    untracked: list[str] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return not (self.added or self.modified or self.deleted or self.untracked)

    @property
    def total(self) -> int:
        return len(self.added) + len(self.modified) + len(self.deleted) + len(self.untracked)


def analyze_diff(start: str | None = None) -> DiffSummary:
    info = scan_git(start)
    summary = DiffSummary()
    if not info.is_repo or info.root is None:
        return summary

    import subprocess

    result = subprocess.run(
        ["git", "-C", str(info.root), "status", "--porcelain"],
        capture_output=True,
        text=True,
        check=False,
    )
    for raw in result.stdout.splitlines():
        if len(raw) < 3:
            continue
        code = raw[:2]
        path = raw[3:]
        if code == "??":
            summary.untracked.append(path)
        elif "D" in code:
            summary.deleted.append(path)
        elif "A" in code:
            summary.added.append(path)
        elif "R" in code:
            summary.modified.append(path)
        elif "M" in code:
            summary.modified.append(path)
    return summary
