"""Provider budget management."""

from __future__ import annotations

from typing import Any


class BudgetManager:
    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config.get("budget", {})

    def daily_limit(self, provider: str) -> int:
        return int(self.config.get("daily_limit", {}).get(provider, 0))

    def check(self, provider: str, used_tokens: int) -> str:
        limit = self.daily_limit(provider)
        if limit <= 0:
            return "normal"
        ratio = used_tokens / limit
        stop = int(self.config.get("stop_threshold", 100)) / 100
        warning = int(self.config.get("warning_threshold", 80)) / 100
        if ratio >= stop:
            return "stop"
        if ratio >= warning:
            return "warning"
        return "normal"
