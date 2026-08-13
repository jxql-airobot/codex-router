"""Run an agent workflow with shared context and optional retry."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from orchestrator.agent_manager import AgentManager
from orchestrator.task_queue import Task, TaskQueue
from orchestrator.workflow import Workflow


@dataclass
class WorkflowRun:
    success: bool
    outputs: dict[str, Any] = field(default_factory=dict)
    history: list[dict[str, Any]] = field(default_factory=list)


class Supervisor:
    def __init__(self, manager: AgentManager) -> None:
        self.manager = manager

    def run(self, task: str, workflow: Workflow, context: dict[str, Any] | None = None) -> WorkflowRun:
        context = dict(context or {})
        queue = TaskQueue()
        run = WorkflowRun(success=True)

        for index, agent_name in enumerate(workflow.steps):
            for attempt in range(workflow.max_round if workflow.retry_enabled else 1):
                item = Task(
                    id=f"{index}-{agent_name}",
                    name=task,
                    agent=agent_name,
                    payload={"context": context},
                )
                queue.push(item)
                agent = self.manager.get(agent_name)
                result = agent.execute(task, context)
                queue.update(item.id, "completed" if result.success else "failed", result.metadata)
                run.history.append(
                    {
                        "agent": agent_name,
                        "attempt": attempt + 1,
                        "success": result.success,
                        "output": result.output,
                    }
                )
                if result.success:
                    run.outputs[agent_name] = result.output
                    context[agent_name] = result.output
                    break
                if attempt == (workflow.max_round if workflow.retry_enabled else 1) - 1:
                    run.success = False
            if not run.success:
                break

        return run
