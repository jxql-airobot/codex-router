"""Token tracking facade."""

from __future__ import annotations

from pathlib import Path

from usage.calculator import CostCalculator
from usage.database import UsageDatabase
from usage.models import UsageRecord


class UsageTracker:
    def __init__(self, db_path: str | Path | None = None, pricing_path: str | Path | None = None) -> None:
        self.database = UsageDatabase(db_path)
        self.calculator = CostCalculator(pricing_path)

    def track(self, record: UsageRecord) -> UsageRecord:
        if record.total_tokens == 0:
            record.total_tokens = record.input_tokens + record.output_tokens + record.cached_tokens
        record.cost = self.calculator.calculate(
            record.model,
            record.input_tokens,
            record.output_tokens,
            record.cached_tokens,
        )
        self.database.insert(record)
        return record

    def close(self) -> None:
        self.database.close()
