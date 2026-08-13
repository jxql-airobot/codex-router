"""Tests for the Codex native hook integration (advisory, fail-open)."""

from __future__ import annotations

import contextlib
import io
import json
import os
import sqlite3
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
    load_agents_md,
    read_stdin_json,
    safe_run,
)
from hooks.before_task import planning_level
from hooks.on_error import looks_like_error
from hooks.store import HookStore


class HookTestCase(unittest.TestCase):
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


class StdinJsonTests(HookTestCase):
    def test_valid_dict(self):
        with mock.patch("sys.stdin", io.StringIO('{"a": 1}')):
            self.assertEqual(read_stdin_json(), {"a": 1})

    def test_empty_input(self):
        with mock.patch("sys.stdin", io.StringIO("")):
            self.assertEqual(read_stdin_json(), {})

    def test_invalid_json(self):
        with mock.patch("sys.stdin", io.StringIO("not json")):
            self.assertEqual(read_stdin_json(), {})

    def test_non_dict_json(self):
        with mock.patch("sys.stdin", io.StringIO("[1, 2, 3]")):
            self.assertEqual(read_stdin_json(), {})


class ExtractTests(HookTestCase):
    def test_full_payload(self):
        info = extract(
            {
                "session_id": "s1",
                "cwd": "/tmp/proj",
                "model": "deepseek",
                "hook_event_name": "UserPromptSubmit",
                "prompt": "hello",
                "reason": "other",
                "source": "startup",
            }
        )
        self.assertEqual(info["session_id"], "s1")
        self.assertEqual(info["cwd"], "/tmp/proj")
        self.assertEqual(info["model"], "deepseek")
        self.assertEqual(info["prompt"], "hello")

    def test_missing_fields_default(self):
        info = extract({})
        self.assertEqual(info["session_id"], "")
        self.assertEqual(info["prompt"], "")
        self.assertEqual(info["model"], _common.DEFAULT_MODEL)

    def test_user_prompt_fallback(self):
        info = extract({"user_prompt": "abc", "model": ""})
        self.assertEqual(info["prompt"], "abc")


class ProjectDetectionTests(HookTestCase):
    def test_basename(self):
        self.assertEqual(detect_project("/workspace/AI-Robot-Demo"), "AI-Robot-Demo")

    def test_marker_file(self):
        marker = Path(self._tmp.name) / "proj" / ".codex-router-project.json"
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text('{"name": "MyProject"}', encoding="utf-8")
        self.assertEqual(detect_project(str(marker.parent)), "MyProject")

    def test_empty(self):
        self.assertEqual(detect_project(""), "")


class AgentsMdTests(HookTestCase):
    def test_present(self):
        p = Path(self._tmp.name) / "proj"
        p.mkdir(parents=True, exist_ok=True)
        (p / "AGENTS.md").write_text("# Project rules", encoding="utf-8")
        self.assertEqual(load_agents_md(str(p)), "# Project rules")

    def test_missing(self):
        self.assertEqual(load_agents_md(str(self._tmp.name)), "")


class EmitContextTests(HookTestCase):
    def test_continue_true(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit_additional_context("hello", "UserPromptSubmit")
        data = json.loads(buf.getvalue())
        self.assertTrue(data["continue"])
        self.assertEqual(
            data["hookSpecificOutput"]["hookEventName"], "UserPromptSubmit"
        )

    def test_contains_text(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit_additional_context("suggestion-abc", "SessionStart")
        self.assertIn("suggestion-abc", buf.getvalue())

    def test_empty_no_output(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit_additional_context("")
        self.assertEqual(buf.getvalue(), "")


class HookStoreTests(HookTestCase):
    def test_tables_created(self):
        store = HookStore()
        tables = store.list_tables()
        self.assertTrue({"classifications", "errors", "session_events"} <= tables)

    def test_record_classification(self):
        store = HookStore()
        store.record_classification(
            "s1", "/w", "p", "task", {"type": "development", "domain": "robotics"}
        )
        self.assertEqual(store.count("classifications"), 1)

    def test_record_error(self):
        store = HookStore()
        store.record_error("s1", "/w", "p", "PostToolUse", "boom")
        self.assertEqual(store.count("errors"), 1)

    def test_record_session(self):
        store = HookStore()
        store.record_session("s1", "/w", "p", "deepseek", "SessionEnd")
        self.assertEqual(store.count("session_events"), 1)


class PlanningLevelTests(HookTestCase):
    def test_level_0(self):
        self.assertEqual(planning_level({"complexity": 2}), 0)

    def test_level_1(self):
        self.assertEqual(planning_level({"complexity": 5}), 1)

    def test_level_2(self):
        self.assertEqual(planning_level({"complexity": 9}), 2)


class BeforeTaskTests(HookTestCase):
    def test_classifies_and_records(self):
        from hooks.before_task import run

        out = self._run_hook(
            run,
            {
                "hook_event_name": "UserPromptSubmit",
                "session_id": "s1",
                "cwd": str(Path(self._tmp.name) / "AI-Robot-Demo"),
                "model": "deepseek",
                "prompt": "给AI-Robot-Demo增加ROS2通信模块",
            },
        )
        self.assertEqual(HookStore().count("classifications"), 1)
        self.assertIn("codex-router", out)
        self.assertIn("任务分析", out)
        self.assertNotIn('"continue": false', out)

    def test_empty_prompt_noop(self):
        from hooks.before_task import run

        out = self._run_hook(
            run,
            {"hook_event_name": "UserPromptSubmit", "session_id": "s1", "prompt": ""},
        )
        self.assertEqual(out, "")
        self.assertEqual(HookStore().count("classifications"), 0)

    def test_classifier_failure_fail_open(self):
        from hooks.before_task import run

        with mock.patch(
            "classification.task_classifier.classify_task",
            side_effect=RuntimeError("boom"),
        ):
            out = self._run_hook(
                run,
                {
                    "hook_event_name": "UserPromptSubmit",
                    "session_id": "s1",
                    "prompt": "anything",
                },
            )
        self.assertEqual(HookStore().count("classifications"), 1)
        self.assertIn("codex-router", out)


class AfterTaskTests(HookTestCase):
    def test_records_tool_event_and_usage(self):
        from hooks.after_task import run

        self._run_hook(
            run,
            {
                "hook_event_name": "PostToolUse",
                "session_id": "s1",
                "cwd": str(Path(self._tmp.name) / "p"),
                "model": "deepseek-v4-pro",
                "tool_name": "Bash",
                "tool_input": "pytest",
                "tool_response": "32 passed",
                "usage": {"input_tokens": 10, "output_tokens": 20, "total_tokens": 30},
            },
        )
        self.assertEqual(HookStore().count("tool_events"), 1)
        conn = sqlite3.connect(str(get_data_dir() / "usage.db"))
        try:
            n = conn.execute("SELECT COUNT(*) FROM usage_records").fetchone()[0]
        finally:
            conn.close()
        self.assertEqual(n, 1)

    def test_ignores_non_tool_event(self):
        from hooks.after_task import run

        self._run_hook(
            run,
            {"hook_event_name": "SessionEnd", "session_id": "s1", "tool_name": "Bash"},
        )
        self.assertEqual(HookStore().count("tool_events"), 0)

    def test_empty_payload_noop(self):
        from hooks.after_task import run

        self._run_hook(run, {})
        self.assertEqual(HookStore().count("tool_events"), 0)


class SessionEndTests(HookTestCase):
    def test_records_summary_and_session(self):
        from hooks.session_end import run

        self._run_hook(
            run,
            {
                "hook_event_name": "SessionEnd",
                "session_id": "s1",
                "cwd": str(Path(self._tmp.name) / "p"),
                "model": "deepseek",
                "reason": "other",
            },
        )
        self.assertEqual(HookStore().count("session_events"), 1)
        self.assertEqual(HookStore().count("session_summaries"), 1)

    def test_empty_payload_fail_open(self):
        from hooks.session_end import run

        self._run_hook(run, {})
        self.assertEqual(HookStore().count("session_summaries"), 1)


class OnErrorTests(HookTestCase):
    def test_detects_traceback(self):
        from hooks.on_error import run

        self._run_hook(
            run,
            {
                "hook_event_name": "PostToolUse",
                "session_id": "s1",
                "cwd": str(Path(self._tmp.name) / "p"),
                "tool_name": "Bash",
                "tool_response": "Traceback (most recent call last): boom",
            },
        )
        self.assertEqual(HookStore().count("errors"), 1)

    def test_ignores_clean_output(self):
        from hooks.on_error import run

        self._run_hook(
            run,
            {
                "hook_event_name": "PostToolUse",
                "session_id": "s1",
                "tool_name": "Bash",
                "tool_response": "32 passed",
            },
        )
        self.assertEqual(HookStore().count("errors"), 0)

    def test_ignores_non_tool_event(self):
        from hooks.on_error import run

        self._run_hook(
            run,
            {
                "hook_event_name": "SessionEnd",
                "session_id": "s1",
                "tool_response": "Traceback boom",
            },
        )
        self.assertEqual(HookStore().count("errors"), 0)


class ErrorMarkerTests(HookTestCase):
    def test_string_true(self):
        self.assertTrue(looks_like_error("fatal: no space left"))

    def test_dict_true(self):
        self.assertTrue(looks_like_error({"error": "denied"}))

    def test_clean_false(self):
        self.assertFalse(looks_like_error("all tests passed"))


class SafeRunTests(HookTestCase):
    def test_swallows_exception(self):
        def boom() -> None:
            raise RuntimeError("boom")

        with self.assertRaises(SystemExit) as ctx:
            safe_run(boom)
        self.assertEqual(ctx.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
