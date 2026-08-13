"""Generic OpenAI-compatible provider."""

from __future__ import annotations

import os
from typing import Any

from providers.base import BaseProvider


class OpenAICompatibleProvider(BaseProvider):
    name = "openai_compatible"
    base_url = ""
    default_model = ""
    api_key_env = ""

    def __init__(self) -> None:
        self.api_key = os.environ.get(self.api_key_env, "")

    def chat(self, messages: list[dict[str, str]], model: str | None = None, **kwargs: Any) -> str:
        if not self.api_key:
            return f"{self.name} 未配置 API key（{self.api_key_env}）"
        # Real HTTP implementation is intentionally deferred; the routing and
        # fallback layers are provider-agnostic.
        return f"{self.name}:{model or self.default_model} response"
