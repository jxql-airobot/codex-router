"""Mock provider for offline health/fallback testing."""

from __future__ import annotations

from typing import Any

from providers.base import BaseProvider


class MockProvider(BaseProvider):
    name = "mock"

    def __init__(
        self,
        name: str = "mock",
        status: str = "available",
        balance: str = "normal",
        quota: str = "normal",
        error: Exception | None = None,
    ) -> None:
        self.name = name
        self.status = status
        self.balance = balance
        self.quota = quota
        self.error = error

    def chat(self, messages, model=None, **kwargs) -> str:
        if self.error:
            raise self.error
        return f"{self.name}:ok"

    def health_check(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "balance": self.balance,
            "quota": self.quota,
        }

    def get_balance(self) -> str:
        return self.balance

    def get_quota(self) -> str:
        return self.quota
