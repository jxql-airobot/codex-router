"""Load enabled agent adapters from configuration."""

from __future__ import annotations

import importlib
from typing import Any

from agents.base_agent import BaseAgent


def load_enabled_agents(config: dict[str, Any]) -> dict[str, BaseAgent]:
    registry_cfg = config.get("agent_adapters", {})
    agents: dict[str, BaseAgent] = {}

    for name, cfg in registry_cfg.items():
        if not isinstance(cfg, dict) or not cfg.get("enabled"):
            continue
        class_path = cfg.get("class")
        if not class_path:
            continue
        module_name, _, class_name = class_path.rpartition(".")
        module = importlib.import_module(module_name)
        adapter_class = getattr(module, class_name)
        kwargs = dict(cfg.get("options", {}) or {})
        if "config" not in kwargs:
            kwargs["config"] = config
        agents[name] = adapter_class(**kwargs)

    return agents


def main() -> int:
    from config_loader import load_config
    from pathlib import Path

    config = load_config(Path(__file__).with_name("config.yaml"))
    agents = load_enabled_agents(config)
    for name, agent in agents.items():
        print(f"- {name}: {type(agent).__name__}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
