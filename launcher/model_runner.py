"""Build and execute the underlying ``codex`` command."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class RunPlan:
    command: list[str]
    env: dict[str, str]

    def as_shell(self) -> str:
        import shlex

        return " ".join(shlex.quote(part) for part in self.command)


def resolve_codex_bin(name: str) -> str:
    """Find a Windows-compatible ``codex`` launcher when available."""
    if os.name == "nt" and name.lower() == "codex":
        for candidate in ("codex.cmd", "codex.exe", "codex.bat"):
            found = shutil.which(candidate)
            if found:
                return found

    found = shutil.which(name)
    if found and found.lower().endswith(".ps1"):
        sibling = Path(found).with_suffix(".cmd")
        if sibling.exists():
            return str(sibling)
    return found or name


def _user_overrides_model(codex_args: list[str]) -> bool:
    """Detect explicit ``-m/--model``, ``-p/--profile``, or ``-c model=`` args."""
    for i, arg in enumerate(codex_args):
        if arg in {"-m", "--model", "-p", "--profile"}:
            return True
        if arg == "-c" and i + 1 < len(codex_args):
            if codex_args[i + 1].split("=", 1)[0] == "model":
                return True
    return False


def build_command(
    selection: Any,
    task: str,
    codex_args: list[str],
    config: dict[str, Any],
) -> RunPlan:
    """Build the codex command from a model selection and config."""
    launcher = config.get("launcher", {})
    models = config.get("models", {})
    model_cfg = models.get(selection.tier, {}) if isinstance(models, dict) else {}

    model_id = (
        model_cfg.get("model")
        or model_cfg.get("model_name")
        or selection.model_name
    )
    provider = model_cfg.get("provider") or selection.provider
    profile = model_cfg.get("profile") or (
        (launcher.get("profiles") or {}).get(selection.tier)
    )
    switch = launcher.get("model_switch", "cli")
    mode = launcher.get("mode", "exec")
    codex_bin = resolve_codex_bin(launcher.get("codex_bin", "codex"))

    command = [codex_bin]
    if mode == "exec":
        command.append("exec")

    model_args: list[str] = []
    env_extra: dict[str, str] = {}

    if not _user_overrides_model(codex_args):
        if switch == "cli":
            model_args = ["-m", model_id]
            if launcher.get("pass_provider") and provider not in ("", "openai"):
                model_args += ["-c", f"model_provider={provider}"]
        elif switch == "config":
            model_args = ["-c", f"model={model_id}"]
            if provider:
                model_args += ["-c", f"model_provider={provider}"]
        elif switch == "profile":
            if not profile:
                raise ValueError(
                    f"model_switch=profile 但模型 {selection.tier!r} 未配置 profile"
                )
            model_args = ["-p", profile]
        elif switch == "env":
            env_extra = {str(k): str(v) for k, v in (model_cfg.get("env") or {}).items()}
            env_extra.setdefault("MODEL_NAME", str(model_id))
            if provider:
                env_extra.setdefault("MODEL_PROVIDER", str(provider))
        else:
            raise ValueError(f"未知 model_switch: {switch!r}")

    command.extend(codex_args)
    command.extend(model_args)
    command.append(task)
    return RunPlan(command=command, env=env_extra)


def run(plan: RunPlan, dry_run: bool = False) -> int:
    if dry_run:
        print("dry-run:", plan.as_shell())
        if plan.env:
            print("env:", plan.env)
        return 0

    env = os.environ.copy()
    env.update(plan.env)
    return subprocess.call(plan.command, env=env)
