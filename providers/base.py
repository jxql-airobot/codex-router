"""Unified provider interface for the multi-provider AI team."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseProvider(ABC):
    name: str = "base"

    @abstractmethod
    def chat(self, messages: list[dict[str, str]], model: str | None = None, **kwargs: Any) -> str:
        raise NotImplementedError

    def health_check(self) -> dict[str, Any]:
        return {"status": "available", "balance": "unknown", "quota": "unknown"}

    def get_balance(self) -> str:
        return "unknown"

    def get_quota(self) -> str:
        return "unknown"
