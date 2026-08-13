"""Generic OpenAI-compatible provider."""

from __future__ import annotations

import os
import json
import urllib.request
import urllib.error
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

        payload = {
            "model": model or self.default_model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.7),
        }
        endpoint = self.base_url.rstrip("/") + "/chat/completions"
        request = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=kwargs.get("timeout", 60)) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            return f"{self.name} API 错误 {exc.code}: {exc.reason}"
        except Exception as exc:
            return f"{self.name} 请求失败: {exc}"

        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            return str(data)
