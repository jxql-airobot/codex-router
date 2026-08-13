"""Build a unified project context for routing and codex prompts."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from memory.project_scanner import ProjectScan, scan_project


MAX_INSTRUCTION_CHARS = 4000


@dataclass
class ProjectContext:
    project_name: str
    root: str
    tech_stack: list[str]
    files: dict[str, str | None]
    git_status: dict[str, Any]
    recent_changes: list[str]
    instructions: str
    score_bonus: int = 0
    bonus_reason: str = ""

    def to_markdown(self) -> str:
        lines = [
            "[Project Context]",
            f"Project: {self.project_name}",
        ]
        if self.tech_stack:
            lines.append("Stack: " + ", ".join(self.tech_stack))
        branch = self.git_status.get("branch")
        if branch:
            lines.append(f"Branch: {branch}")
        dirty = self.git_status.get("dirty_files") or []
        if dirty:
            lines.append(f"Uncommitted files: {len(dirty)}")
        if self.recent_changes:
            lines.append("Recent:")
            for change in self.recent_changes[:3]:
                lines.append(f"- {change}")
        if self.instructions.strip():
            lines.append("Instructions:")
            lines.append(self.instructions.strip())
        return "\n".join(lines)

    def to_display(self) -> str:
        lines = [
            "[Project Context]",
            f"Project: {self.project_name}",
        ]
        if self.tech_stack:
            lines.append("Stack: " + ", ".join(self.tech_stack))
        if self.recent_changes:
            lines.append("Recent: " + self.recent_changes[0])
        return "\n".join(lines)


def _read_limited(path: Path, limit: int) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")[:limit]
    except OSError:
        return ""


def compute_score_bonus(scan: ProjectScan) -> tuple[int, str]:
    bonus = 0
    reasons: list[str] = []
    stack = set(scan.tech_stack)

    if "ROS2" in stack:
        bonus += 15
        reasons.append("ROS2项目")
    if "Gazebo" in stack:
        bonus += 10
        reasons.append("Gazebo仿真")
    if "YOLO" in stack:
        bonus += 10
        reasons.append("YOLO视觉")
    if scan.file_count >= 50:
        bonus += 10
        reasons.append(f"{scan.file_count}个文件")
    if len(scan.git.dirty_files) >= 5:
        bonus += 10
        reasons.append("5+个未提交改动")

    bonus = min(bonus, 30)
    return bonus, "、".join(reasons) if reasons else ""


def build_context(
    start: str | Path | None = None,
    max_instruction_chars: int = MAX_INSTRUCTION_CHARS,
) -> ProjectContext:
    scan: ProjectScan = scan_project(start)

    instructions_parts: list[str] = []
    for marker in ("AGENTS.md", "PROJECT_STATUS.md", "ARCHITECTURE.md"):
        path = scan.markers.get(marker)
        if path:
            text = _read_limited(path, max_instruction_chars)
            if text.strip():
                instructions_parts.append(text.strip())

    recent = list(scan.git.recent_commits)
    status_path = scan.markers.get("PROJECT_STATUS.md")
    if not recent and status_path:
        status_text = _read_limited(status_path, 1200)
        first_line = next(
            (line.strip() for line in status_text.splitlines() if line.strip()),
            "",
        )
        if first_line:
            recent = [first_line]

    bonus, reason = compute_score_bonus(scan)
    return ProjectContext(
        project_name=scan.project_name,
        root=str(scan.root),
        tech_stack=scan.tech_stack,
        files={name: (str(path) if path else None) for name, path in scan.markers.items()},
        git_status={
            "is_repo": scan.git.is_repo,
            "branch": scan.git.branch,
            "dirty_files": scan.git.dirty_files,
            "recent_commits": scan.git.recent_commits,
        },
        recent_changes=recent,
        instructions="\n\n".join(instructions_parts),
        score_bonus=bonus,
        bonus_reason=reason,
    )
