"""Unified agent interface for pluggable model providers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class AgentResult:
    ok: bool
    output: str = ""
    metadata: dict = field(default_factory=dict)


class BaseAgent(ABC):
    name: str = "base"

    def analyze(self, task: str) -> str:
        return task

    @abstractmethod
    def execute(self, task: str, context: str = "") -> AgentResult:
        raise NotImplementedError

    def review(self, result: AgentResult) -> AgentResult:
        return result
