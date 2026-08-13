"""Classify task intent."""

from __future__ import annotations


def classify_intent(features: dict) -> str:
    if features.get("has_list") and (
        features.get("files") or features.get("actions") or features.get("has_output_requirements")
    ):
        return "explicit"
    if features.get("has_list"):
        return "semi"
    return "goal"
