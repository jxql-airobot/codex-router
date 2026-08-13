"""Local model provider adapter placeholder."""

from __future__ import annotations

from agents.base_agent import AgentResult, BaseAgent


class LocalAgentAdapter(BaseAgent):
    name = "local"

    def __init__(self, config: dict | None = None):
        self.config = config or {}

    def execute(self, task: str, context: str = "") -> AgentResult:
        return AgentResult(
            success=False,
            output="Local adapter 已注册，但默认关闭；可接入 Ollama / LM Studio。",
            metadata={"provider": "local"},
        )
