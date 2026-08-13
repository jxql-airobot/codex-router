"""OpenAI provider."""

from __future__ import annotations

from providers.openai_compatible import OpenAICompatibleProvider


class OpenAIProvider(OpenAICompatibleProvider):
    name = "openai"
    base_url = "https://api.openai.com/v1"
    default_model = "gpt-4.1"
    api_key_env = "OPENAI_API_KEY"
