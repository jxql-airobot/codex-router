"""Shared helpers for codex-router hooks.

Every hook must be fail-open: it must never raise out of the entrypoint,
never emit ``continue: false``, and always exit 0 on unexpected errors so the
official Codex flow is never blocked.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

DEFAULT_MODEL = "deepseek"


def _force_utf8_io() -> None:
    """Force UTF-8 on std streams so Chinese payload/output never mojibakes.

    Codex pipes the hook payload and reads hook stdout as UTF-8. On Windows the
    Python default is often the locale code page (GBK), which corrupts Chinese
    text in both directions. This is best-effort and never raises.
    """
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass


_force_utf8_io()


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


def now_iso() -> str:
    """Return a UTC ISO-8601 timestamp, never raises."""
    try:
        return datetime.now(timezone.utc).isoformat()
    except Exception:
        return ""


def summarize(value: Any, limit: int = 200) -> str:
    """Turn a payload value into a short, single-line text summary."""
    try:
        if value is None:
            return ""
        if isinstance(value, (dict, list)):
            text = json.dumps(value, ensure_ascii=False)
        else:
            text = str(value)
        text = " ".join(text.split())
        if len(text) > limit:
            return text[:limit] + "..."
        return text
    except Exception:
        return ""


def git_status(cwd: str, timeout: float = 2.0) -> str:
    """Return a compact git working-tree summary, or "" when unavailable."""
    if not cwd:
        return ""
    try:
        result = subprocess.run(
            ["git", "-C", str(cwd), "status", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except Exception:
        return ""
    if result.returncode != 0:
        return ""
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    if not lines:
        return "clean"
    counts = {"modified": 0, "added": 0, "deleted": 0, "renamed": 0, "untracked": 0}
    for line in lines:
        code = line[:2]
        if code == "??":
            counts["untracked"] += 1
            continue
        status = code.strip()
        if "M" in status:
            counts["modified"] += 1
        if "A" in status:
            counts["added"] += 1
        if "D" in status:
            counts["deleted"] += 1
        if "R" in status:
            counts["renamed"] += 1
    parts = [f"{k}:{v}" for k, v in counts.items() if v]
    return ",".join(parts) if parts else "clean"


def token_usage(payload: dict[str, Any]) -> dict[str, int]:
    """Extract token counts from a hook payload defensively."""
    usage = payload.get("usage")
    if not isinstance(usage, dict):
        usage = {}

    def _int(*keys: str) -> int:
        for key in keys:
            try:
                value = int(usage.get(key, 0))
            except Exception:
                continue
            if value > 0:
                return value
        return 0

    input_tokens = _int("input_tokens", "prompt_tokens", "input")
    output_tokens = _int("output_tokens", "completion_tokens", "output")
    total_tokens = _int("total_tokens", "total")
    if total_tokens == 0:
        total_tokens = input_tokens + output_tokens
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
    }


def log_hook(message: str) -> None:
    """Append one line to the hook log; never raises."""
    try:
        path = get_data_dir() / "hooks.log"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(f"{now_iso()} {message}\n")
    except Exception:
        pass


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
