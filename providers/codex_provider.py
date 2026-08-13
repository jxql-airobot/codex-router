"""Provider that delegates to the installed Codex CLI."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from providers.base_provider import LLMProvider


class CodexProvider(LLMProvider):
    name = "codex"

    def __init__(self, codex_bin: str = "codex-real", model: str = "deepseek-v4-flash"):
        self.codex_bin = codex_bin
        self.model = model

    def generate(self, prompt: str) -> str:
        result = subprocess.run(
            [self.codex_bin, "exec", "-m", self.model, prompt],
            capture_output=True,
            text=True,
            check=False,
        )
        return (result.stdout or result.stderr).strip()

    def chat(self, messages: list[dict[str, str]]) -> str:
        prompt = "\n".join(
            f"{message.get('role', 'user')}: {message.get('content', '')}"
            for message in messages
        )
        return self.generate(prompt)
