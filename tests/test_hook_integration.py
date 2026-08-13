"""Integration tests for the Codex native hook layer.

Covers hook loading, all three wired events, fail-open degradation, path and
API failure handling, and the shared helpers used by every hook.
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from hooks import _common
from hooks._common import (
    detect_project,
    emit_additional_context,
    extract,
    get_data_dir,
    git_status,
    load_agents_md,
    read_stdin_json,
    safe_run,
    summarize,
    token_usage,
)
from hooks.store import HookStore


class HookIntegrationTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self._old_env = os.environ.get("CODEX_ROUTER_DATA_DIR")
        os.environ["CODEX_ROUTER_DATA_DIR"] = self._tmp.name
        self.addCleanup(self._restore_env)

    def _restore_env(self) -> None:
        if self._old_env is None:
            os.environ.pop("CODEX_ROUTER_DATA_DIR", None)
        else:
            os.environ["CODEX_ROUTER_DATA_DIR"] = self._old_env

    def _run_hook(self, fn, payload: dict) -> str:
        buf = io.StringIO()
        fake_stdin = io.StringIO(json.dumps(payload, ensure_ascii=False))
        with mock.patch("sys.stdin", fake_stdin):
            with contextlib.redirect_stdout(buf):
                fn()
        return buf.getvalue()

    def _payload(self, **overrides) -> dict:
        payload = {
            "hook_event_name": "UserPromptSubmit",
            "session_id": "s1",
            "cwd": str(Path(self._tmp.name) / "AI-Robot-Demo"),
            "model": "deepseek-v4-pro",
            "prompt": "给AI-Robot-Demo增加ROS2通信模块",
        }
        payload.update(overrides)
        return payload

    def _make_git_repo(self) -> str:
        path = Path(self._tmp.name) / "repo"
        path.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "init", "-q", str(path)], check=False)
        return str(path)


class HookLoadingTests(HookIntegrationTestCase):
    def test_before_task_importable(self):
        import hooks.before_task  # noqa: F401

    def test_after_task_importable(self):
        import hooks.after_task  # noqa: F401

    def test_session_end_importable(self):
        import hooks.session_end  # noqa: F401

    def test_on_error_importable(self):
        import hooks.on_error  # noqa: F401

    def test_all_hooks_have_run(self):
        import hooks.after_task
        import hooks.before_task
        import hooks.on_error
        import hooks.session_end

        for module in (
            hooks.before_task,
            hooks.after_task,
            hooks.session_end,
            hooks.on_error,
        ):
            self.assertTrue(callable(getattr(module, "run")))


class UserPromptSubmitTriggerTests(HookIntegrationTestCase):
    def test_classifies_and_emits_context(self):
        from hooks.before_task import run

        out = self._run_hook(run, self._payload())
        data = json.loads(out)
        self.assertTrue(data["continue"])
        self.assertIn("codex-router", out)
        self.assertIn("任务分析", out)
        self.assertEqual(HookStore().count("classifications"), 1)

    def test_empty_prompt_is_noop(self):
        from hooks.before_task import run

        out = self._run_hook(run, self._payload(prompt=""))
        self.assertEqual(out, "")
        self.assertEqual(HookStore().count("classifications"), 0)

    def test_classifier_failure_fails_open(self):
        from hooks.before_task import run

        with mock.patch(
            "classification.task_classifier.classify_task",
            side_effect=RuntimeError("boom"),
        ):
            out = self._run_hook(run, self._payload())
        self.assertIn("codex-router", out)
        self.assertEqual(HookStore().count("classifications"), 1)

    def test_chinese_prompt_survives(self):
        from hooks.before_task import run

        out = self._run_hook(run, self._payload(prompt="修复机器人导航错误"))
        self.assertNotIn("continue\": false", out)
        self.assertEqual(HookStore().count("classifications"), 1)

    def test_emit_additional_context_shape(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit_additional_context("suggestion", "UserPromptSubmit")
        data = json.loads(buf.getvalue())
        self.assertEqual(data["hookSpecificOutput"]["hookEventName"], "UserPromptSubmit")
        self.assertEqual(data["hookSpecificOutput"]["additionalContext"], "suggestion")


class PostToolUseTriggerTests(HookIntegrationTestCase):
    def test_records_tool_event(self):
        from hooks.after_task import run

        self._run_hook(
            run,
            self._payload(
                hook_event_name="PostToolUse",
                tool_name="Bash",
                tool_input="pytest",
                tool_response="32 passed",
            ),
        )
        self.assertEqual(HookStore().count("tool_events"), 1)

    def test_records_usage_database(self):
        from hooks.after_task import run

        self._run_hook(
            run,
            self._payload(
                hook_event_name="PostToolUse",
                tool_name="Bash",
                tool_response="ok",
                usage={"input_tokens": 5, "output_tokens": 7},
            ),
        )
        conn = sqlite3.connect(str(get_data_dir() / "usage.db"))
        try:
            n = conn.execute("SELECT COUNT(*) FROM usage_records").fetchone()[0]
        finally:
            conn.close()
        self.assertEqual(n, 1)

    def test_ignores_session_end_event(self):
        from hooks.after_task import run

        self._run_hook(
            run,
            self._payload(hook_event_name="SessionEnd", tool_name="Bash"),
        )
        self.assertEqual(HookStore().count("tool_events"), 0)

    def test_empty_payload_is_noop(self):
        from hooks.after_task import run

        self._run_hook(run, {})
        self.assertEqual(HookStore().count("tool_events"), 0)

    def test_marks_failure_from_traceback(self):
        from hooks.after_task import run

        self._run_hook(
            run,
            self._payload(
                hook_event_name="PostToolUse",
                tool_name="Bash",
                tool_response="Traceback (most recent call last): boom",
            ),
        )
        conn = sqlite3.connect(str(get_data_dir() / "hook_events.db"))
        try:
            row = conn.execute(
                "SELECT success FROM tool_events ORDER BY id DESC LIMIT 1"
            ).fetchone()
        finally:
            conn.close()
        self.assertEqual(row[0], 0)

    def test_usage_failure_fails_open(self):
        from hooks.after_task import run

        with mock.patch(
            "usage.database.UsageDatabase.insert",
            side_effect=RuntimeError("db down"),
        ):
            self._run_hook(
                run,
                self._payload(
                    hook_event_name="PostToolUse",
                    tool_name="Bash",
                    tool_response="ok",
                ),
            )
        self.assertEqual(HookStore().count("tool_events"), 1)


class SessionEndTriggerTests(HookIntegrationTestCase):
    def test_records_summary_and_session_event(self):
        from hooks.session_end import run

        self._run_hook(run, self._payload(hook_event_name="SessionEnd", reason="other"))
        self.assertEqual(HookStore().count("session_events"), 1)
        self.assertEqual(HookStore().count("session_summaries"), 1)

    def test_aggregates_tool_and_error_counts(self):
        store = HookStore()
        store.record_tool_event("s1", "/w", "p", "Bash")
        store.record_error("s1", "/w", "p", "PostToolUse", "boom")
        store.record_classification("s1", "/w", "p", "task", {"type": "development"})

        from hooks.session_end import run

        self._run_hook(run, self._payload(hook_event_name="SessionEnd"))
        conn = sqlite3.connect(str(get_data_dir() / "hook_events.db"))
        try:
            row = conn.execute(
                "SELECT tool_count, error_count FROM session_summaries "
                "WHERE session_id='s1' ORDER BY id DESC LIMIT 1"
            ).fetchone()
        finally:
            conn.close()
        self.assertEqual(row[0], 1)
        self.assertEqual(row[1], 1)

    def test_empty_payload_fails_open(self):
        from hooks.session_end import run

        self._run_hook(run, {})
        self.assertEqual(HookStore().count("session_summaries"), 1)

    def test_writes_project_memory(self):
        from hooks.session_end import run

        self._run_hook(run, self._payload(hook_event_name="SessionEnd"))
        self.assertTrue((get_data_dir() / "project_memory.json").exists())


class DegradationTests(HookIntegrationTestCase):
    def test_read_stdin_invalid_json(self):
        with mock.patch("sys.stdin", io.StringIO("not-json")):
            self.assertEqual(read_stdin_json(), {})

    def test_read_stdin_empty(self):
        with mock.patch("sys.stdin", io.StringIO("")):
            self.assertEqual(read_stdin_json(), {})

    def test_extract_missing_fields(self):
        info = extract({})
        self.assertEqual(info["session_id"], "")
        self.assertEqual(info["model"], _common.DEFAULT_MODEL)

    def test_detect_project_missing_dir(self):
        self.assertEqual(detect_project(str(Path(self._tmp.name) / "nope")), "nope")

    def test_load_agents_md_missing(self):
        self.assertEqual(load_agents_md(str(Path(self._tmp.name) / "nope")), "")

    def test_git_status_missing_dir(self):
        self.assertEqual(git_status(str(Path(self._tmp.name) / "nope")), "")

    def test_safe_run_swallows_exception(self):
        def boom() -> None:
            raise RuntimeError("boom")

        with self.assertRaises(SystemExit) as ctx:
            safe_run(boom)
        self.assertEqual(ctx.exception.code, 0)


class SharedHelperTests(HookIntegrationTestCase):
    def test_summarize_string(self):
        self.assertEqual(summarize("  hello world  "), "hello world")

    def test_summarize_dict(self):
        self.assertEqual(summarize({"a": 1}), '{"a": 1}')

    def test_summarize_truncates(self):
        self.assertTrue(summarize("x" * 300, limit=200).endswith("..."))

    def test_summarize_none(self):
        self.assertEqual(summarize(None), "")

    def test_token_usage_full(self):
        usage = token_usage(
            {"usage": {"input_tokens": 3, "output_tokens": 4, "total_tokens": 7}}
        )
        self.assertEqual(usage, {"input_tokens": 3, "output_tokens": 4, "total_tokens": 7})

    def test_token_usage_partial_fallback(self):
        usage = token_usage({"usage": {"prompt_tokens": 2, "completion_tokens": 5}})
        self.assertEqual(usage["input_tokens"], 2)
        self.assertEqual(usage["output_tokens"], 5)
        self.assertEqual(usage["total_tokens"], 7)

    def test_token_usage_absent(self):
        self.assertEqual(token_usage({}), {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0})

    def test_git_status_clean_repo(self):
        self.assertEqual(git_status(self._make_git_repo()), "clean")

    def test_log_hook_writes_file(self):
        _common.log_hook("hello-log")
        log_path = get_data_dir() / "hooks.log"
        self.assertTrue(log_path.exists())
        self.assertIn("hello-log", log_path.read_text(encoding="utf-8"))


class HookStoreIntegrationTests(HookIntegrationTestCase):
    def test_tables_created(self):
        tables = HookStore().list_tables()
        self.assertTrue(
            {
                "classifications",
                "errors",
                "session_events",
                "tool_events",
                "session_summaries",
            }
            <= tables
        )

    def test_record_tool_event(self):
        store = HookStore()
        store.record_tool_event("s1", "/w", "p", "Bash", task="t", total_tokens=9)
        self.assertEqual(store.count("tool_events"), 1)

    def test_record_session_summary(self):
        store = HookStore()
        store.record_session_summary(
            "s1", "/w", "p", "deepseek", "summary", recent_tasks=["a", "b"]
        )
        self.assertEqual(store.count("session_summaries"), 1)

    def test_latest_task(self):
        store = HookStore()
        store.record_classification("s1", "/w", "p", "first", {"type": "x"})
        store.record_classification("s1", "/w", "p", "second", {"type": "x"})
        self.assertEqual(store.latest_task("s1"), "second")

    def test_latest_task_missing(self):
        self.assertEqual(HookStore().latest_task("none"), "")

    def test_session_stats(self):
        store = HookStore()
        store.record_tool_event("s1", "/w", "p", "Bash")
        store.record_error("s1", "/w", "p", "PostToolUse", "boom")
        store.record_classification("s1", "/w", "p", "task", {"type": "x"})
        stats = store.session_stats("s1")
        self.assertEqual(stats["tool_count"], 1)
        self.assertEqual(stats["error_count"], 1)
        self.assertEqual(stats["recent_tasks"], ["task"])


class OnErrorStandbyTests(HookIntegrationTestCase):
    def test_detects_traceback(self):
        from hooks.on_error import run

        self._run_hook(
            run,
            self._payload(
                hook_event_name="PostToolUse",
                tool_name="Bash",
                tool_response="fatal: no space left",
            ),
        )
        self.assertEqual(HookStore().count("errors"), 1)

    def test_ignores_clean_output(self):
        from hooks.on_error import run

        self._run_hook(
            run,
            self._payload(
                hook_event_name="PostToolUse",
                tool_name="Bash",
                tool_response="all tests passed",
            ),
        )
        self.assertEqual(HookStore().count("errors"), 0)


if __name__ == "__main__":
    unittest.main()
