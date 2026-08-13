"""DeepSeek provider placeholder (OpenAI-compatible API)."""

from __future__ import annotations

from providers.base_provider import LLMProvider


class DeepSeekProvider(LLMProvider):
    name = "deepseek"

    def __init__(self, api_key: str | None = None, model: str = "deepseek-chat"):
        self.api_key = api_key
        self.model = model

    def generate(self, prompt: str) -> str:
        if not self.api_key:
            return "DeepSeek provider 未配置 API key。"
        return "DeepSeek provider 尚未实现真实 API 调用。"

    def chat(self, messages: list[dict[str, str]]) -> str:
        return self.generate("\n".join(m.get("content", "") for m in messages))
