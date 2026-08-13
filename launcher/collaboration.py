"""Framework primitives for parallel multi-agent collaboration."""

from __future__ import annotations

from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Callable

from launcher.execution_mode import AgentRole


@dataclass
class TaskAssignment:
    agent: str
    task: str
    context: str = ""


@dataclass
class AgentOutput:
    agent: str
    output: str
    changed_files: list[str] = field(default_factory=list)


def plan_parallel_tasks(
    task: str,
    roles: list[AgentRole],
) -> list[TaskAssignment]:
    """Split one task into one assignment per role."""
    return [
        TaskAssignment(agent=role.name, task=task, context=role.instructions)
        for role in roles
    ]


def run_parallel(
    assignments: list[TaskAssignment],
    worker: Callable[[TaskAssignment], AgentOutput],
    max_workers: int = 4,
) -> list[AgentOutput]:
    """Run assignments concurrently and return completed outputs."""
    outputs: list[AgentOutput] = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(worker, assignment): assignment for assignment in assignments}
        for future in as_completed(futures):
            outputs.append(future.result())
    return outputs


def merge_outputs(outputs: list[AgentOutput]) -> str:
    lines: list[str] = ["# Collaboration Result"]
    for output in outputs:
        lines.append(f"\n## {output.agent}\n{output.output.strip()}")
    return "\n".join(lines)


def detect_file_conflicts(
    outputs: list[AgentOutput],
) -> dict[str, list[str]]:
    """Return files changed by more than one agent."""
    owners: dict[str, list[str]] = defaultdict(list)
    for output in outputs:
        for path in output.changed_files:
            owners[path].append(output.agent)
    return {path: agents for path, agents in owners.items() if len(agents) > 1}
