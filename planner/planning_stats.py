"""Planner token-saving statistics."""

from __future__ import annotations

from collections import Counter
from typing import Iterable


def savings_from_levels(levels: Iterable[int]) -> dict:
    counter = Counter(levels)
    total = sum(counter.values()) or 1
    direct = counter[0]
    organize = counter[1]
    full = counter[2]
    return {
        "total": total,
        "direct": direct,
        "organize": organize,
        "full": full,
        "direct_ratio": direct / total,
        "organize_ratio": organize / total,
        "full_ratio": full / total,
        "estimated_savings": round((direct * 1.0 + organize * 0.5) / total * 100, 1),
    }
