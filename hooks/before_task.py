"""before_task hook: classify an incoming task and surface advisory context.

Mapped to the official ``UserPromptSubmit`` event. This hook only analyses and
suggests; it never changes the active model or blocks the turn.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from hooks._common import (
    detect_project,
    emit_additional_context,
    extract,
    load_agents_md,
    log_hook,
    read_stdin_json,
    safe_run,
)
from hooks.store import HookStore


def planning_level(result: dict) -> int:
    complexity = int(result.get("complexity", 0))
    if complexity <= 3:
        return 0
    if complexity <= 7:
        return 1
    return 2


def build_suggestion(result: dict, has_context: bool) -> str:
    suggestion = (
        "[codex-router] 任务分析: 类型=%s, 领域=%s, 复杂度=%s/10, "
        "建议模式=%s, 建议Agent=%s, 规划级别=%s。"
        % (
            result.get("type", "development"),
            result.get("domain", "general"),
            result.get("complexity", 0),
            result.get("recommended_workflow", "developer"),
            ",".join(result.get("recommended_agents", ["coder"])),
            result.get("planning_level", 0),
        )
    )
    if has_context:
        suggestion += " 已加载项目 AGENTS.md 上下文。"
    return suggestion


def run() -> None:
    payload = read_stdin_json()
    info = extract(payload)
    prompt = info["prompt"]
    if not prompt:
        return

    cwd = info["cwd"]
    project = detect_project(cwd)
    model = info["model"]
    started = time.monotonic()

    try:
        from classification.task_mode import classify_mode

        mode = classify_mode(prompt)
    except Exception:
        mode = {"mode": "complex", "reason": "classifier_failure", "confidence": 0.0}

    latency_ms = int((time.monotonic() - started) * 1000)
    HookStore().record_route(
        info["session_id"],
        cwd,
        project,
        prompt,
        mode["mode"],
        mode.get("reason", ""),
        latency_ms,
    )

    # Fast path: skip the heavy pipeline, add no model context.
    if mode["mode"] == "fast":
        log_hook(
            f"FastPath session={info['session_id']} project={project} "
            f"reason={mode.get('reason')} latency={latency_ms}ms"
        )
        return

    # Complex path: run the full analysis and surface advisory context.
    try:
        from classification.task_classifier import classify_task

        result = classify_task(prompt, {"project_name": project})
    except Exception:
        result = {
            "type": "development",
            "domain": "general",
            "complexity": 0,
            "recommended_workflow": "developer",
            "recommended_agents": ["coder"],
            "recommended_model": model,
        }

    result["recommended_model"] = model
    result["planning_level"] = planning_level(result)

    HookStore().record_classification(info["session_id"], cwd, project, prompt, result)

    has_context = bool(load_agents_md(cwd))
    emit_additional_context(build_suggestion(result, has_context), info["event"])
    log_hook(
        f"ComplexPath session={info['session_id']} project={project} "
        f"type={result.get('type')} complexity={result.get('complexity')} "
        f"latency={latency_ms}ms"
    )


if __name__ == "__main__":
    safe_run(run)
