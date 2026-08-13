"""Git agent wraps git_manager into the agent interface."""

from __future__ import annotations

from typing import Any

from agents.base import AgentResult, BaseAgent
from git_manager.commit_generator import generate_commit_message
from git_manager.diff_analyzer import analyze_diff
from git_manager.scanner import scan_git


class GitAgent(BaseAgent):
    name = "git"
    description = "分析改动并生成 commit 建议"
    capabilities = ["git_status", "diff_analysis", "commit_generation"]

    def execute(self, task: str, context: dict[str, Any] | str = "") -> AgentResult:
        repo = context.get("repo") if isinstance(context, dict) else None
        info = scan_git(repo)
        diff = analyze_diff(repo)
        message = generate_commit_message(diff)
        if diff.is_empty:
            return AgentResult(success=False, output="no changes to commit")
        return AgentResult(
            success=True,
            output=message,
            metadata={
                "branch": info.branch,
                "changed_files": diff.total,
                "message": message,
            },
        )
