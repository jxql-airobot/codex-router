"""Control the autonomous loop with a retry limit."""

from __future__ import annotations


def run_loop(runner, max_retry: int = 5) -> bool:
    for _ in range(max_retry):
        result = runner()
        if result.ok:
            return True
    return False
