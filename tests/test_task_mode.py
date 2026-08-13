"""Tests for fast/complex task-mode routing classifier."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from classification.task_mode import classify_mode


class FastModeTests(unittest.TestCase):
    def test_greeting(self):
        self.assertEqual(classify_mode("你好")["mode"], "fast")

    def test_output_number(self):
        self.assertEqual(classify_mode("输出1")["mode"], "fast")

    def test_version(self):
        self.assertEqual(classify_mode("查看版本")["mode"], "fast")

    def test_explain_error(self):
        self.assertEqual(classify_mode("解释错误")["mode"], "fast")

    def test_english_greeting(self):
        self.assertEqual(classify_mode("hello")["mode"], "fast")

    def test_english_thanks(self):
        self.assertEqual(classify_mode("thanks")["mode"], "fast")

    def test_short_numeric(self):
        self.assertEqual(classify_mode("12345")["mode"], "fast")

    def test_special_chars(self):
        self.assertEqual(classify_mode("!!!??")["mode"], "fast")

    def test_short_input_reason(self):
        self.assertEqual(classify_mode("随便写点东西")["reason"], "short_input")

    def test_fast_confidence_in_range(self):
        confidence = classify_mode("你好")["confidence"]
        self.assertGreaterEqual(confidence, 0.0)
        self.assertLessEqual(confidence, 1.0)


class ComplexModeTests(unittest.TestCase):
    def test_modify_code(self):
        self.assertEqual(classify_mode("修改Python代码")["mode"], "complex")

    def test_design_architecture(self):
        self.assertEqual(classify_mode("设计ROS2架构")["mode"], "complex")

    def test_develop_agent(self):
        self.assertEqual(classify_mode("开发Agent系统")["mode"], "complex")

    def test_refactor_project(self):
        self.assertEqual(classify_mode("重构项目")["mode"], "complex")

    def test_fix_bug(self):
        self.assertEqual(classify_mode("fix bug")["mode"], "complex")

    def test_add_test(self):
        self.assertEqual(classify_mode("添加测试")["mode"], "complex")

    def test_file_path(self):
        self.assertEqual(classify_mode("修改 src/main.py")["mode"], "complex")

    def test_multi_step(self):
        self.assertEqual(classify_mode("完成以下5个功能")["mode"], "complex")

    def test_run_test(self):
        self.assertEqual(classify_mode("运行测试")["mode"], "complex")

    def test_complex_reason(self):
        self.assertEqual(classify_mode("修改代码")["reason"], "code_change")

    def test_complex_confidence_in_range(self):
        confidence = classify_mode("重构项目")["confidence"]
        self.assertGreaterEqual(confidence, 0.0)
        self.assertLessEqual(confidence, 1.0)


class EdgeCaseTests(unittest.TestCase):
    def test_empty_input(self):
        result = classify_mode("")
        self.assertEqual(result["mode"], "fast")
        self.assertEqual(result["reason"], "empty_input")

    def test_whitespace_input(self):
        self.assertEqual(classify_mode("   ")["mode"], "fast")

    def test_none_input(self):
        self.assertEqual(classify_mode(None)["mode"], "fast")

    def test_long_input_no_keyword(self):
        long_text = "啊" * 60
        self.assertEqual(classify_mode(long_text)["mode"], "complex")

    def test_long_input_reason(self):
        long_text = "a" * 60
        self.assertEqual(classify_mode(long_text)["reason"], "long_input")

    def test_chinese_code_term(self):
        self.assertEqual(classify_mode("实现功能")["mode"], "complex")

    def test_english_code_term(self):
        self.assertEqual(classify_mode("implement feature")["mode"], "complex")

    def test_always_returns_dict(self):
        self.assertIsInstance(classify_mode("anything"), dict)

    def test_mode_values_only(self):
        for text in ["你好", "修改代码", "hello", "重构", "?", ""]:
            self.assertIn(classify_mode(text)["mode"], ("fast", "complex"))


if __name__ == "__main__":
    unittest.main()
