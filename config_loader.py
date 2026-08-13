"""Configuration loading with sensible launcher defaults."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


DEFAULT_LAUNCHER: dict[str, Any] = {
    "codex_bin": "codex",
    "mode": "exec",
    "model_switch": "cli",
    "pass_provider": False,
}


def load_config(path: str | Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}

    data.setdefault("auto_router", True)
    data.setdefault("default_model", "flash")
    data.setdefault("models", {})
    data.setdefault("threshold", {})
    data.setdefault("launcher", {})

    for key, value in DEFAULT_LAUNCHER.items():
        data["launcher"].setdefault(key, value)

    # Give every model a stable ``model`` id even if only ``model_name`` exists.
    for tier, model in data["models"].items():
        if isinstance(model, dict):
            model.setdefault("model", model.get("model_name"))
            model.setdefault("provider", "")
            model.setdefault("env", {})
            model.setdefault("profile", None)

    return data
