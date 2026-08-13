"""Unified developer-agent interface.

All developer agents inherit from :class:`BaseAgent` and return
:class:`AgentResult`. Agents must not bind themselves to a specific provider;
they receive provider access through the orchestrator when needed.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentResult:
    success: bool = False
    output: str = ""
    artifacts: list[Any] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseAgent(ABC):
    name: str = "base"
    description: str = ""
    capabilities: list[str] = []

    @abstractmethod
    def execute(self, task: str, context: dict[str, Any] | str = "") -> AgentResult:
        raise NotImplementedError
