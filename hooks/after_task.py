"""after_task hook: record PostToolUse tool executions.

Mapped to the official ``PostToolUse`` event with a ``^Bash$`` matcher. It is
advisory only: it records tool activity, token usage, provider/model metadata
and git state into SQLite, and always fails open so the Codex turn never blocks.
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
    extract,
    get_data_dir,
    git_status,
    log_hook,
    read_stdin_json,
    safe_run,
    summarize,
    token_usage,
)
from hooks.on_error import looks_like_error
from hooks.store import HookStore


def infer_provider(model: str) -> str:
    lowered = model.lower()
    if "deepseek" in lowered:
        return "deepseek"
    if "gpt" in lowered or "openai" in lowered:
        return "openai"
    if "claude" in lowered:
        return "anthropic"
    if "gemini" in lowered:
        return "google"
    return "unknown"


def run() -> None:
    payload = read_stdin_json()
    info = extract(payload)
    if info["event"] not in ("PostToolUse", "PreToolUse"):
        return

    started = time.monotonic()
    tool_name = str(payload.get("tool_name") or "unknown")
    tool_response = payload.get("tool_response")
    tool_input = payload.get("tool_input")
    cwd = info["cwd"]
    project = detect_project(cwd)

    store = HookStore()
    task = store.latest_task(info["session_id"]) or summarize(tool_input, limit=300)
    usage = token_usage(payload)
    result_summary = summarize(tool_response, limit=500)
    status = git_status(cwd)
    success = not looks_like_error(tool_response)
    duration_ms = int((time.monotonic() - started) * 1000)

    store.record_tool_event(
        session_id=info["session_id"],
        cwd=cwd,
        project=project,
        tool_name=tool_name,
        task=task,
        result_summary=result_summary,
        model=info["model"],
        provider=infer_provider(info["model"]),
        input_tokens=usage["input_tokens"],
        output_tokens=usage["output_tokens"],
        total_tokens=usage["total_tokens"],
        git_status=status,
        duration_ms=duration_ms,
        success=success,
    )

    try:
        from usage.database import UsageDatabase
        from usage.models import UsageRecord

        db = UsageDatabase(db_path=get_data_dir() / "usage.db")
        try:
            db.insert(
                UsageRecord(
                    project=project,
                    task=task or tool_name,
                    model=info["model"],
                    provider=infer_provider(info["model"]),
                    input_tokens=usage["input_tokens"],
                    output_tokens=usage["output_tokens"],
                    total_tokens=usage["total_tokens"],
                    task_id=info["session_id"],
                    success=success,
                )
            )
        finally:
            db.close()
    except Exception:
        pass

    log_hook(
        f"PostToolUse session={info['session_id']} tool={tool_name} "
        f"tokens={usage['total_tokens']} git={status} success={success}"
    )


if __name__ == "__main__":
    safe_run(run)
