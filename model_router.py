"""Role-based provider routing for the AI team."""

from __future__ import annotations

from typing import Any

from providers.base import BaseProvider
from providers.deepseek_provider import DeepSeekProvider
from providers.moonshot_provider import MoonshotProvider
from providers.openai_provider import OpenAIProvider
from providers.qwen_provider import QwenProvider
from providers.zhipu_provider import ZhipuProvider


ROLE_KEYWORDS = {
    "architect": ["设计", "架构", "方案", "技术路线", "技术选型"],
    "coder": ["实现", "修改", "添加功能", "重构", "开发"],
    "reviewer": ["检查", "review", "优化", "分析问题", "审查"],
    "researcher": ["论文", "调研", "对比", "文献"],
    "knowledge": ["pdf", "文档", "手册", "知识库"],
    "tester": ["测试", "报错", "修复", "测试失败"],
}

PROVIDER_CLASSES: dict[str, type[BaseProvider]] = {
    "openai": OpenAIProvider,
    "deepseek": DeepSeekProvider,
    "zhipu": ZhipuProvider,
    "moonshot": MoonshotProvider,
    "qwen": QwenProvider,
}


def detect_role(task: str) -> str:
    text = task.lower()
    for role, keywords in ROLE_KEYWORDS.items():
        if any(keyword.lower() in text for keyword in keywords):
            return role
    return "coder"


def route_role(task: str, config: dict[str, Any]) -> dict[str, Any]:
    role = detect_role(task)
    routing = config.get("role_routing", {}).get(role, {})
    fallback = config.get("fallback", {}).get(role, [])
    return {
        "role": role,
        "provider": routing.get("provider", "deepseek"),
        "model": routing.get("model", ""),
        "fallback": fallback,
    }


def load_provider(name: str, config: dict[str, Any] | None = None) -> BaseProvider:
    provider_cls = PROVIDER_CLASSES.get(name)
    if provider_cls is None:
        raise KeyError(f"unknown provider: {name}")
    return provider_cls()


def fallback_chain(role: str, config: dict[str, Any]) -> list[str]:
    return list(config.get("fallback", {}).get(role, []))
