"""Text-based AI model status center (fallback when no GUI)."""

from __future__ import annotations

from providers.status import emoji_for


def render_status(providers: list[dict] | None = None) -> str:
    providers = providers or [
        {"name": "GPT", "status": "available"},
        {"name": "DeepSeek", "status": "available"},
        {"name": "Qwen", "status": "warning"},
        {"name": "GLM", "status": "unavailable"},
    ]
    lines = ["AI模型状态中心"]
    for provider in providers:
        lines.append(
            f"{provider['name']}: {emoji_for(provider['status'])} {provider['status']}"
        )
    return "\n".join(lines)
