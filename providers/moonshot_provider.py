"""Moonshot (Kimi) provider."""

from __future__ import annotations

from providers.openai_compatible import OpenAICompatibleProvider


class MoonshotProvider(OpenAICompatibleProvider):
    name = "moonshot"
    base_url = "https://api.moonshot.cn/v1"
    default_model = "moonshot-v1-8k"
    api_key_env = "MOONSHOT_API_KEY"
