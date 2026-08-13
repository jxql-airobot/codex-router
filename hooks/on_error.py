"""on_error hook: detect failed tool calls and record them.

Standby helper. It is intentionally NOT bound to ``PostToolUse`` by default:
normal tool completion is handled by ``after_task.py``. Error detection is
heuristic and the hook always fails open (exit 0).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from hooks._common import detect_project, extract, read_stdin_json, safe_run
from hooks.store import HookStore

ERROR_MARKERS = (
    "traceback",
    "exception",
    "error:",
    "failed",
    "failure",
    "non-zero exit",
    "no such file",
    "command not found",
    "cannot",
    "fatal:",
    "denied",
)


def looks_like_error(tool_response) -> bool:
    if isinstance(tool_response, str):
        text = tool_response
    elif isinstance(tool_response, dict):
        text = json.dumps(tool_response, ensure_ascii=False)
    else:
        text = str(tool_response or "")
    low = text.lower()
    return any(marker in low for marker in ERROR_MARKERS)


def run() -> None:
    payload = read_stdin_json()
    info = extract(payload)
    if info["event"] not in ("PostToolUse", "PreToolUse"):
        return
    tool_response = payload.get("tool_response")
    if not looks_like_error(tool_response):
        return

    project = detect_project(info["cwd"])
    tool_name = payload.get("tool_name") or "unknown"
    detail = f"{tool_name}: {str(tool_response)[:500]}"
    HookStore().record_error(
        info["session_id"], info["cwd"], project, info["event"], detail
    )


if __name__ == "__main__":
    safe_run(run)
