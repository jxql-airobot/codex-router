"""Run Codex as an agent through the existing model runner."""

from __future__ import annotations

import os
import subprocess
from typing import Any

from agents.base_agent import AgentResult, BaseAgent
from launcher.model_runner import build_command


class CodexAgentAdapter(BaseAgent):
    name = "codex"

    def __init__(self, model_tier: str = "flash", config: dict[str, Any] | None = None):
        self.model_tier = model_tier
        self.config = config or {}

    def execute(self, task: str, context: str = "") -> AgentResult:
        import tempfile
        from types import SimpleNamespace

        model_cfg = self.config.get("models", {}).get(self.model_tier, {})
        model_id = model_cfg.get("model") or model_cfg.get("model_name") or self.model_tier
        provider = model_cfg.get("provider", "")
        selection = SimpleNamespace(
            tier=self.model_tier,
            model_name=model_id,
            provider=provider,
        )

        prompt = f"{context}\n\n# 用户任务\n{task}".strip()
        with tempfile.NamedTemporaryFile(
            "w", suffix=".md", delete=False, encoding="utf-8"
        ) as handle:
            handle.write(prompt)
            output_file = handle.name

        plan = build_command(
            selection,
            prompt,
            ["--output-last-message", output_file],
            self.config,
        )
        code = subprocess.call(plan.command)

        output = ""
        if os.path.exists(output_file):
            try:
                output = open(output_file, encoding="utf-8").read()
            except OSError:
                output = ""
            try:
                os.remove(output_file)
            except OSError:
                pass

        return AgentResult(ok=code == 0, output=output, metadata={"code": code})
