"""Agent registry and lifecycle."""

from __future__ import annotations

from typing import Any

from agents.base import BaseAgent


class AgentManager:
    def __init__(self) -> None:
        self._agents: dict[str, BaseAgent] = {}

    def register(self, agent: BaseAgent) -> None:
        self._agents[agent.name] = agent

    def get(self, name: str) -> BaseAgent:
        if name not in self._agents:
            raise KeyError(f"unknown agent: {name}")
        return self._agents[name]

    def names(self) -> list[str]:
        return list(self._agents.keys())

    def describe(self) -> list[dict[str, Any]]:
        return [
            {
                "name": agent.name,
                "description": agent.description,
                "capabilities": agent.capabilities,
            }
            for agent in self._agents.values()
        ]
