"""DeepSeek provider adapter (OpenAI-compatible API placeholder)."""

from __future__ import annotations

from agents.base_agent import AgentResult, BaseAgent


class DeepSeekAgentAdapter(BaseAgent):
    name = "deepseek"

    def __init__(self, config: dict | None = None):
        self.config = config or {}

    def execute(self, task: str, context: str = "") -> AgentResult:
        return AgentResult(
            success=False,
            output="DeepSeek adapter 已注册，但尚未绑定 API key；请在 config.yaml 配置后调用。",
            metadata={"provider": "deepseek"},
        )
