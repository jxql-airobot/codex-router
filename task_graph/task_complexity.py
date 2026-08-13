"""Signals used to decide whether a task needs decomposition."""

from __future__ import annotations

import re

from planner.task_analyzer import detect_file_paths, detect_task_list


DOMAIN_KEYWORDS = {
    "ros2": ["ros2", "机器人", "导航", "话题", "gazebo"],
    "rag": ["rag", "知识库", "检索", "文档"],
    "plc": ["plc", "工业自动化", "automation"],
    "agent": ["agent", "智能体", "多agent"],
    "paper": ["论文", "实验", "调研"],
    "web": ["web", "前端", "后端", "api"],
    "data": ["数据", "分析", "可视化"],
}

FORBIDDEN_KEYWORDS = [
    "修改配置",
    "更新readme",
    "修复报错",
    "修复登录",
    "生成报告",
    "格式转换",
    "增加一个接口参数",
]

MUST_KEYWORDS = [
    "开发系统",
    "机器人agent系统",
    "平台",
    "工业机器人",
    "跨领域",
    "多agent",
    "多模块",
]


def detect_domains(text: str) -> set[str]:
    lower = text.lower()
    return {
        name for name, keywords in DOMAIN_KEYWORDS.items()
        if any(keyword.lower() in lower for keyword in keywords)
    }


def file_count(text: str) -> int:
    return len(set(detect_file_paths(text)))


def has_dependency_words(text: str) -> bool:
    return any(word in text for word in ("然后", "之后", "先", "再", "架构", "设计", "依赖"))


def has_user_steps(text: str) -> bool:
    return detect_task_list(text)


def is_forbidden(text: str) -> bool:
    lower = text.lower()
    return any(keyword.lower() in lower for keyword in FORBIDDEN_KEYWORDS)


def is_must_decompose(text: str) -> bool:
    lower = text.lower()
    return any(keyword.lower() in lower for keyword in MUST_KEYWORDS)
