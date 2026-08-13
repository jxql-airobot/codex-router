"""DeepSeek provider."""

from __future__ import annotations

from providers.openai_compatible import OpenAICompatibleProvider


class DeepSeekProvider(OpenAICompatibleProvider):
    name = "deepseek"
    base_url = "https://api.deepseek.com/v1"
    default_model = "deepseek-chat"
    api_key_env = "DEEPSEEK_API_KEY"

    def generate(self, prompt: str) -> str:
        return self.chat([{"role": "user", "content": prompt}])
