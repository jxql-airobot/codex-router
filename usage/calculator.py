"""Cost calculation from configurable pricing."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


class CostCalculator:
    def __init__(self, pricing_path: str | Path | None = None) -> None:
        self.pricing_path = Path(
            pricing_path or (Path(__file__).resolve().parents[1] / "config" / "pricing.yaml")
        )
        self.pricing: dict[str, Any] = yaml.safe_load(self.pricing_path.read_text(encoding="utf-8")) or {}

    def calculate(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cached_tokens: int = 0,
    ) -> float:
        cfg = self.pricing.get("models", {}).get(model, {})
        input_price = float(cfg.get("input_price_per_1m", 0))
        output_price = float(cfg.get("output_price_per_1m", 0))
        cache_price = float(cfg.get("cache_price_per_1m", 0))
        return (
            input_tokens * input_price
            + output_tokens * output_price
            + cached_tokens * cache_price
        ) / 1_000_000
