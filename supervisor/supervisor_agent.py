"""Top-level supervisor that dynamically builds and coordinates a team."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from supervisor.agent_selector import select_agents
from supervisor.result_merger import merge_results
from supervisor.task_analyzer import analyze_task
from supervisor.team_builder import build_team
from supervisor.workflow_planner import plan_tasks
from team.team_state import AgentState


@dataclass
class SupervisorResult:
    task: str
    analysis: dict[str, Any] = field(default_factory=dict)
    team: list[dict[str, Any]] = field(default_factory=list)
    tasks: list[dict[str, Any]] = field(default_factory=list)
    outputs: dict[str, Any] = field(default_factory=dict)
    success: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "task": self.task,
            "analysis": self.analysis,
            "team": self.team,
            "tasks": self.tasks,
            "outputs": self.outputs,
            "success": self.success,
        }


class SupervisorAgent:
    name = "supervisor"

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or {}

    def run(self, task: str, project: str = "") -> SupervisorResult:
        analysis = analyze_task(task, project)
        agents = select_agents(analysis)
        team = build_team(agents, self.config)
        tasks = plan_tasks(task, team)
        states = [AgentState(agent=member["name"]) for member in team]
        outputs = {
            state.agent: f"mock:{state.agent}"
            for state in states
        }
        return SupervisorResult(
            task=task,
            analysis=analysis,
            team=team,
            tasks=tasks,
            outputs=outputs,
        )
