"""Qwen (DashScope) provider."""

from __future__ import annotations

from providers.openai_compatible import OpenAICompatibleProvider


class QwenProvider(OpenAICompatibleProvider):
    name = "qwen"
    base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    default_model = "qwen-plus"
    api_key_env = "DASHSCOPE_API_KEY"
