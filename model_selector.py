"""Model selection logic for the Codex model router."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from config_loader import load_config

# Re-export so existing callers and tests can keep using
# ``from model_selector import load_config``.
__all__ = ["ModelInfo", "load_config", "select"]


@dataclass
class ModelInfo:
    tier: str
    provider: str
    model_name: str
    mode: str
    reason: str


def select(
    score: int,
    config: dict[str, Any],
    override: str | None = None,
) -> ModelInfo:
    """Choose Flash or Pro from the score and optional manual override."""
    threshold_pro = int(config["threshold"]["pro_score"])
    models = config["models"]
    default_tier = config.get("default_model", "flash")

    if override and override.lower() != "auto":
        tier = override.lower()
        if tier not in models:
            raise ValueError(
                f"未知模型覆盖值: {override!r}（可选 flash / pro / auto）"
            )
        model = models[tier]
        return ModelInfo(
            tier=tier,
            provider=model["provider"],
            model_name=model["model_name"],
            mode="forced",
            reason=f"人工强制使用 {tier}",
        )

    tier = "pro" if score >= threshold_pro else default_tier
    model = models[tier]
    if tier == "pro":
        reason = f"复杂度 {score}/100 >= Pro 阈值 {threshold_pro}"
    else:
        reason = f"复杂度 {score}/100 < Pro 阈值 {threshold_pro}，使用默认模型"

    return ModelInfo(
        tier=tier,
        provider=model["provider"],
        model_name=model["model_name"],
        mode="auto",
        reason=reason,
    )
