"""Gemini provider adapter placeholder."""

from __future__ import annotations

from agents.base_agent import AgentResult, BaseAgent


class GeminiAgentAdapter(BaseAgent):
    name = "gemini"

    def __init__(self, config: dict | None = None):
        self.config = config or {}

    def execute(self, task: str, context: str = "") -> AgentResult:
        return AgentResult(
            ok=False,
            output="Gemini adapter 已注册，但默认关闭；启用后配置 API key 即可使用。",
            metadata={"provider": "gemini"},
        )
