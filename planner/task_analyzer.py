"""Analyze whether a task already contains an executable plan."""

from __future__ import annotations

import re
from typing import Any


def detect_task_list(text: str) -> bool:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    numbered = sum(bool(re.match(r"^\d+[\.、)]", line)) for line in lines)
    chinese_steps = sum("第" in line and "步" in line for line in lines)
    return numbered >= 2 or chinese_steps >= 2


def detect_action_keywords(text: str) -> list[str]:
    keywords = ["修改", "添加", "增加", "删除", "实现", "测试", "部署", "运行"]
    return [keyword for keyword in keywords if keyword in text]


def detect_file_paths(text: str) -> list[str]:
    return re.findall(r"[\w./\\-]+\.(?:py|md|yaml|yml|json|toml|sh|ps1|cmd|cpp|h|js|ts)", text)


def detect_output_requirements(text: str) -> bool:
    return any(keyword in text.lower() for keyword in ("提交git", "生成文档", "运行测试", "部署"))


def analyze_task(text: str) -> dict[str, Any]:
    return {
        "has_list": detect_task_list(text),
        "actions": detect_action_keywords(text),
        "files": detect_file_paths(text),
        "has_output_requirements": detect_output_requirements(text),
    }
