"""Experiment orchestration."""

from __future__ import annotations


def run_experiment(config: dict) -> dict:
    return {"config": config, "status": "pending"}
