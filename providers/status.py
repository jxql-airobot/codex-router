"""Provider health status model."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass
class ProviderStatus:
    provider: str
    status: str = "available"
    balance_status: str = "unknown"
    quota_status: str = "unknown"
    last_check: str = ""
    error_count: int = 0

    def __post_init__(self) -> None:
        if not self.last_check:
            self.last_check = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "status": self.status,
            "balance_status": self.balance_status,
            "quota_status": self.quota_status,
            "last_check": self.last_check,
            "error_count": self.error_count,
        }


def emoji_for(status: str) -> str:
    return {
        "available": "🟢",
        "warning": "🟡",
        "limited": "🟠",
        "unavailable": "🔴",
        "unknown": "⚪",
    }.get(status, "⚪")
