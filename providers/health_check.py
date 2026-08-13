"""Health checking helpers independent of real API billing."""

from __future__ import annotations

from typing import Any

from providers.base import BaseProvider
from providers.status import ProviderStatus


def check_provider(provider: BaseProvider, error_count: int = 0) -> ProviderStatus:
    try:
        info = provider.health_check()
    except Exception:
        info = {"status": "unavailable", "balance": "unknown", "quota": "unknown"}
        error_count += 1
    return ProviderStatus(
        provider=provider.name,
        status=info.get("status", "available"),
        balance_status=info.get("balance", "unknown"),
        quota_status=info.get("quota", "unknown"),
        error_count=error_count,
    )


def is_usable(status: ProviderStatus) -> bool:
    return status.status in {"available", "warning", "limited"}


def chinese_warning(status: ProviderStatus, task: str) -> str:
    lines = [
        "⚠️ AI服务额度提醒",
        f"当前模型: {status.provider}",
        f"状态: {'余额不足' if status.balance_status == 'low' else status.status}",
        f"当前任务: {task}",
        "建议:",
        "1. 切换备用模型",
        "2. 充值后继续",
        "3. 暂停任务",
    ]
    return "\n".join(lines)
