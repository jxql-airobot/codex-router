"""Lightweight supervisor orchestration for Agent Mode.

The pipeline is intentionally deterministic and transparent. It uses the real
``codex`` binary (``codex-real``) with a role-specific model and prompt for each
step. Callers can preview every command with ``dry_run=True``.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from launcher.execution_mode import AgentRole, load_roles
from launcher.model_runner import build_command


AGENTS_DIR = Path(__file__).resolve().parents[1] / "agents"


@dataclass
class AgentStep:
    role: AgentRole
    prompt: str
    codex_args: list[str]


def _read_role_doc(name: str) -> str:
    path = AGENTS_DIR / f"{name}.md"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def _build_prompt(
    role: AgentRole,
    task: str,
    context: str,
    project_context: str = "",
) -> str:
    parts: list[str] = []
    if project_context.strip():
        parts.append(project_context.strip())
    role_doc = _read_role_doc(role.name)
    if role_doc.strip():
        parts.append(role_doc.strip())
    parts.append(f"# 当前任务\n{task}")
    if context:
        parts.append(f"# 前序 Agent 输出\n{context}")
    return "\n\n".join(parts)


def build_agent_steps(
    task: str,
    config: dict[str, Any],
    project_context: str = "",
) -> list[AgentStep]:
    """Build the Planner -> Coder -> Tester -> Reviewer pipeline."""
    steps: list[AgentStep] = []
    context = ""

    for role in load_roles(config):
        prompt = _build_prompt(role, task, context, project_context)
        codex_args = []
        if role.sandbox:
            codex_args += ["--sandbox", role.sandbox]

        steps.append(AgentStep(role=role, prompt=prompt, codex_args=codex_args))
        context += f"[{role.name}]\n{prompt}\n"

    return steps


def _model_for_tier(tier: str, config: dict[str, Any]) -> tuple[str, str]:
    model_cfg = config.get("models", {}).get(tier, {})
    model_id = model_cfg.get("model") or model_cfg.get("model_name") or tier
    provider = model_cfg.get("provider", "")
    return model_id, provider


def build_step_command(
    step: AgentStep,
    config: dict[str, Any],
    output_file: str | None = None,
) -> list[str]:
    model_id, provider = _model_for_tier(step.role.model_tier, config)
    selection = SimpleNamespace(
        tier=step.role.model_tier,
        model_name=model_id,
        provider=provider,
    )
    args = list(step.codex_args)
    if output_file:
        args += ["--output-last-message", output_file]
    plan = build_command(selection, step.prompt, args, config)
    return plan.command


def run_agent_pipeline(
    task: str,
    config: dict[str, Any],
    dry_run: bool = False,
    project_context: str = "",
) -> int:
    context = ""
    last_code = 0

    for role in load_roles(config):
        prompt = _build_prompt(role, task, context, project_context)
        codex_args = ["--sandbox", role.sandbox] if role.sandbox else []
        step = AgentStep(role=role, prompt=prompt, codex_args=codex_args)

        output_file: str | None = None
        if not dry_run:
            handle = tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".md",
                prefix=f"{step.role.name}-",
                delete=False,
                encoding="utf-8",
            )
            handle.close()
            output_file = handle.name

        command = build_step_command(step, config, output_file)
        print(f"\n--- {step.role.name.title()} ({step.role.model_tier}) ---")
        if dry_run:
            import shlex

            print(" ".join(shlex.quote(part) for part in command))
            last_code = 0
            continue
        else:
            last_code = subprocess.call(command)

            if output_file and os.path.exists(output_file):
                try:
                    text = Path(output_file).read_text(encoding="utf-8")
                except OSError:
                    text = ""
                context += f"[{step.role.name}]\n{text}\n"
                try:
                    os.remove(output_file)
                except OSError:
                    pass

        if last_code != 0:
            print(f"\n[{step.role.name}] 退出码 {last_code}，停止流水线。")
            return last_code

    return last_code
