"""Run the Git Automation Lifecycle for the current project.

Examples:
    python git_lifecycle.py
    python git_lifecycle.py --commit
    python git_lifecycle.py --commit --push
"""

from __future__ import annotations

import argparse
import sys

from git_manager.commit_generator import generate_commit_message
from git_manager.diff_analyzer import analyze_diff
from git_manager.operator import push, stage_and_commit
from git_manager.scanner import scan_git
from report.generator import generate_report
from task_manager.manager import TaskRecord


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Git Automation Lifecycle")
    parser.add_argument("--repo", help="repository path (default: current directory)")
    parser.add_argument("--type", help="explicit commit type (feat/fix/refactor/docs/test)")
    parser.add_argument("--commit", action="store_true", help="run git add && git commit")
    parser.add_argument("--push", action="store_true", help="push to origin after commit")
    args = parser.parse_args(argv)

    repo = args.repo
    info = scan_git(repo)
    diff = analyze_diff(repo)
    message = generate_commit_message(diff, explicit_type=args.type)

    commit = ""
    push_status = ""
    status = "dry-run"

    if args.commit:
        code, output = stage_and_commit(repo or ".", message)
        if code == 0:
            commit = message
            status = "committed"
        else:
            status = "commit-failed"
            print(output, file=sys.stderr)
            return code

        if args.push:
            code, output = push(repo or ".", info.branch)
            if code == 0:
                push_status = "pushed"
                status = "pushed"
            else:
                push_status = "push-failed"
                status = "push-failed"
                print(output, file=sys.stderr)
                return code

    record = TaskRecord(
        task="git lifecycle",
        model="router",
        mode="git",
        changed_files=(
            diff.added + diff.modified + diff.deleted + diff.untracked
        ),
        tests="",
        commit=commit,
        push=push_status,
        status=status,
    )
    print(generate_report(record))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
