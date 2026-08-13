"""Provider response hook and token estimation."""

from __future__ import annotations

import re
from contextlib import contextmanager
from typing import Iterator

from usage.models import UsageRecord
from usage.tracker import UsageTracker


def estimate_tokens(text: str) -> int:
    words = len(re.findall(r"\S+", text or ""))
    return max(1, int(words * 1.3))


class UsageCollector:
    def __init__(self, tracker: UsageTracker, **record_fields) -> None:
        self.tracker = tracker
        self.fields = record_fields

    def record(self, input_text: str, output_text: str, cached_tokens: int = 0) -> UsageRecord:
        input_tokens = estimate_tokens(input_text)
        output_tokens = estimate_tokens(output_text)
        return self.tracker.track(
            UsageRecord(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cached_tokens=cached_tokens,
                **self.fields,
            )
        )


@contextmanager
def capture_usage(tracker: UsageTracker, **fields) -> Iterator[UsageCollector]:
    collector = UsageCollector(tracker, **fields)
    yield collector
