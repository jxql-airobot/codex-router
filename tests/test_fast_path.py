"""Tests for fast/complex path routing integration in before_task."""

from __future__ import annotations

import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from hooks.store import HookStore


class FastPathTestCase(unittest.TestCase):
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

    def _run(self, payload: dict) -> str:
        from hooks.before_task import run

        buf = io.StringIO()
        fake_stdin = io.StringIO(json.dumps(payload, ensure_ascii=False))
        with mock.patch("sys.stdin", fake_stdin):
            with contextlib.redirect_stdout(buf):
                run()
        return buf.getvalue()


class BeforeTaskRoutingTests(FastPathTestCase):
    def test_fast_path_emits_no_context(self):
        out = self._run(
            {
                "hook_event_name": "UserPromptSubmit",
                "session_id": "s1",
                "cwd": "C:/work/p",
                "model": "deepseek",
                "prompt": "你好",
            }
        )
        self.assertEqual(out, "")

    def test_fast_path_records_fast_route(self):
        self._run(
            {
                "hook_event_name": "UserPromptSubmit",
                "session_id": "s1",
                "cwd": "C:/work/p",
                "model": "deepseek",
                "prompt": "查看版本",
            }
        )
        summary = HookStore().route_summary()
        self.assertEqual(summary["fast"]["count"], 1)
        self.assertEqual(summary["complex"]["count"], 0)

    def test_fast_path_skips_classification(self):
        self._run(
            {
                "hook_event_name": "UserPromptSubmit",
                "session_id": "s1",
                "cwd": "C:/work/p",
                "model": "deepseek",
                "prompt": "输出1",
            }
        )
        self.assertEqual(HookStore().count("classifications"), 0)

    def test_complex_path_emits_context(self):
        out = self._run(
            {
                "hook_event_name": "UserPromptSubmit",
                "session_id": "s1",
                "cwd": "C:/work/p",
                "model": "deepseek",
                "prompt": "修改Python代码",
            }
        )
        self.assertIn("codex-router", out)
        self.assertNotIn('"continue": false', out)

    def test_complex_path_records_complex_route(self):
        self._run(
            {
                "hook_event_name": "UserPromptSubmit",
                "session_id": "s1",
                "cwd": "C:/work/p",
                "model": "deepseek",
                "prompt": "设计ROS2架构",
            }
        )
        summary = HookStore().route_summary()
        self.assertEqual(summary["complex"]["count"], 1)

    def test_complex_path_records_classification(self):
        self._run(
            {
                "hook_event_name": "UserPromptSubmit",
                "session_id": "s1",
                "cwd": "C:/work/p",
                "model": "deepseek",
                "prompt": "开发Agent系统",
            }
        )
        self.assertEqual(HookStore().count("classifications"), 1)

    def test_empty_prompt_noop(self):
        self._run({"hook_event_name": "UserPromptSubmit", "session_id": "s1", "prompt": ""})
        self.assertEqual(HookStore().count("route_stats"), 0)

    def test_classifier_failure_fail_open(self):
        with mock.patch(
            "classification.task_mode.classify_mode",
            side_effect=RuntimeError("boom"),
        ):
            self._run(
                {
                    "hook_event_name": "UserPromptSubmit",
                    "session_id": "s1",
                    "cwd": "C:/work/p",
                    "prompt": "你好",
                }
            )
        summary = HookStore().route_summary()
        self.assertEqual(summary["complex"]["count"], 1)


class RouteStatsStoreTests(FastPathTestCase):
    def test_record_route_and_summary(self):
        store = HookStore()
        store.record_route("s1", "/w", "p", "a", "fast", "simple_question", 30)
        store.record_route("s2", "/w", "p", "b", "complex", "code_change", 90)
        summary = store.route_summary()
        self.assertEqual(summary["fast"]["count"], 1)
        self.assertEqual(summary["complex"]["count"], 1)
        self.assertEqual(summary["fast"]["avg_latency_ms"], 30.0)
        self.assertEqual(summary["complex"]["avg_latency_ms"], 90.0)

    def test_summary_empty(self):
        summary = HookStore().route_summary()
        self.assertEqual(summary["fast"]["count"], 0)
        self.assertEqual(summary["complex"]["count"], 0)


class RouteStatsAnalyticsTests(FastPathTestCase):
    def test_report_percentages(self):
        store = HookStore()
        for _ in range(4):
            store.record_route("s", "/w", "p", "fast", "fast", "short_input", 10)
        store.record_route("s", "/w", "p", "complex", "complex", "code_change", 100)

        from analytics.route_stats import route_stats_report

        report = route_stats_report(store)
        self.assertEqual(report["total"], 5)
        self.assertEqual(report["fast"]["count"], 4)
        self.assertEqual(report["complex"]["count"], 1)
        self.assertAlmostEqual(report["fast"]["percent"], 80.0)
        self.assertAlmostEqual(report["complex"]["percent"], 20.0)

    def test_format_report(self):
        store = HookStore()
        store.record_route("s", "/w", "p", "fast", "fast", "short_input", 3000)
        store.record_route("s", "/w", "p", "complex", "complex", "code_change", 45000)

        from analytics.route_stats import format_report, route_stats_report

        text = format_report(route_stats_report(store))
        self.assertIn("Fast", text)
        self.assertIn("Complex", text)
        self.assertIn("50.0%", text)

    def test_report_empty_total(self):
        from analytics.route_stats import route_stats_report

        report = route_stats_report(HookStore())
        self.assertEqual(report["total"], 0)
        self.assertEqual(report["fast"]["percent"], 0.0)


if __name__ == "__main__":
    unittest.main()
