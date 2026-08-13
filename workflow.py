"""Run the default developer workflow or inspect status."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from agents.coder_agent import CoderAgent
from agents.git_agent import GitAgent
from agents.planner_agent import PlannerAgent
from agents.reviewer_agent import ReviewerAgent
from agents.tester_agent import TesterAgent
from memory.context_builder import build_context
from orchestrator.agent_manager import AgentManager
from orchestrator.supervisor import Supervisor
from orchestrator.workflow import load_workflow


WORKFLOW_PATH = Path(__file__).with_name("workflows") / "developer_workflow.yaml"


def build_manager() -> AgentManager:
    manager = AgentManager()
    manager.register(PlannerAgent())
    manager.register(CoderAgent())
    manager.register(TesterAgent())
    manager.register(ReviewerAgent())
    manager.register(GitAgent())
    return manager


def run_workflow(task: str, repo: str | None = None):
    context = build_context(repo)
    workflow = load_workflow(WORKFLOW_PATH)
    run = Supervisor(build_manager()).run(
        task,
        workflow,
        context={
            "project_name": context.project_name,
            "tech_stack": context.tech_stack,
            "repo": repo,
        },
    )
    return run


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Developer agent workflow")
    parser.add_argument("task", nargs="*")
    parser.add_argument("--repo", help="project path")
    parser.add_argument("--workflow-status", action="store_true")
    args = parser.parse_args(argv)

    if args.workflow_status:
        print("workflow:", " -> ".join(load_workflow(WORKFLOW_PATH).steps))
        print("agents:", build_manager().names())
        return 0

    task = " ".join(args.task).strip()
    if not task:
        print("错误：请提供任务。", file=sys.stderr)
        return 2

    run = run_workflow(task, args.repo)
    print(json.dumps(
        {
            "success": run.success,
            "outputs": run.outputs,
            "history": run.history,
        },
        ensure_ascii=False,
        indent=2,
    ))
    return 0 if run.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
