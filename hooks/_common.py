"""Shared helpers for codex-router hooks.

Every hook must be fail-open: it must never raise out of the entrypoint,
never emit ``continue: false``, and always exit 0 on unexpected errors so the
official Codex flow is never blocked.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Callable

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

DEFAULT_MODEL = "deepseek"


def get_data_dir() -> Path:
    """Return the directory used for hook/usage data (overridable in tests)."""
    env = os.environ.get("CODEX_ROUTER_DATA_DIR")
    if env:
        return Path(env)
    return REPO_ROOT / "data"


def read_stdin_json() -> dict[str, Any]:
    """Read the hook payload from stdin and fail open on any error."""
    try:
        raw = sys.stdin.read()
    except Exception:
        return {}
    if not raw or not raw.strip():
        return {}
    try:
        data = json.loads(raw)
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def extract(payload: dict[str, Any]) -> dict[str, Any]:
    """Extract the fields shared by every hook event, defensively."""
    cwd = payload.get("cwd") or os.getcwd()
    prompt = payload.get("prompt") or payload.get("user_prompt") or ""
    return {
        "session_id": str(payload.get("session_id") or ""),
        "cwd": str(cwd),
        "model": str(payload.get("model") or DEFAULT_MODEL),
        "event": str(payload.get("hook_event_name") or ""),
        "prompt": str(prompt).strip(),
        "reason": str(payload.get("reason") or ""),
        "source": str(payload.get("source") or ""),
    }


def detect_project(cwd: str) -> str:
    """Best-effort project name detection from the session working directory."""
    if not cwd:
        return ""
    path = Path(cwd)
    marker = path / ".codex-router-project.json"
    try:
        if marker.exists():
            data = json.loads(marker.read_text(encoding="utf-8", errors="ignore"))
            if isinstance(data, dict) and data.get("name"):
                return str(data["name"])
    except Exception:
        pass
    return path.name or ""


def load_agents_md(cwd: str, limit: int = 2000) -> str:
    """Load a truncated AGENTS.md snapshot when present."""
    if not cwd:
        return ""
    try:
        text = (Path(cwd) / "AGENTS.md").read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""
    return text[:limit]


def emit_additional_context(text: str, event_name: str = "UserPromptSubmit") -> None:
    """Emit advisory context for the model. Never sets ``continue: false``."""
    if not text:
        return
    output = {
        "continue": True,
        "hookSpecificOutput": {
            "hookEventName": event_name or "UserPromptSubmit",
            "additionalContext": text,
        },
    }
    try:
        print(json.dumps(output, ensure_ascii=False))
    except Exception:
        print(text)


def record_error(
    session_id: str,
    cwd: str,
    project: str,
    event: str,
    detail: str,
) -> None:
    """Persist a hook error observation. Never raises."""
    try:
        from hooks.store import HookStore

        HookStore().record_error(session_id, cwd, project, event, detail)
    except Exception:
        pass


def safe_run(fn: Callable[[], None]) -> None:
    """Run a hook entrypoint and always exit 0 (fail-open)."""
    try:
        fn()
    except Exception as exc:  # noqa: BLE001 - fail-open by design
        record_error("internal", "", "", "hook_exception", str(exc))
    sys.exit(0)
