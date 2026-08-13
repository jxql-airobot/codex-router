"""Build an AI team with responsibilities and models."""

from __future__ import annotations

from typing import Any


RESPONSIBILITIES = {
    "ArchitectAgent": "系统设计与技术选型",
    "RobotAgent": "ROS2/机器人开发",
    "RAGAgent": "知识检索与记忆",
    "CoderAgent": "代码实现",
    "TesterAgent": "测试与验证",
    "ResearchAgent": "研究与实验",
    "PLC_Agent": "PLC 自动化",
}

DEFAULT_MODELS = {
    "ArchitectAgent": "openai",
    "RobotAgent": "deepseek",
    "RAGAgent": "qwen",
    "CoderAgent": "deepseek",
    "TesterAgent": "deepseek",
    "ResearchAgent": "moonshot",
    "PLC_Agent": "deepseek",
}


def model_for_agent(agent: str, config: dict[str, Any] | None = None) -> str:
    config = config or {}
    routing = config.get("role_routing", {})
    role = {
        "ArchitectAgent": "architect",
        "RobotAgent": "coder",
        "RAGAgent": "knowledge",
        "CoderAgent": "coder",
        "TesterAgent": "tester",
        "ResearchAgent": "researcher",
        "PLC_Agent": "coder",
    }.get(agent, "coder")
    return routing.get(role, {}).get("provider") or DEFAULT_MODELS.get(agent, "deepseek")


def build_team(agent_names: list[str], config: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    return [
        {
            "name": name,
            "responsibility": RESPONSIBILITIES.get(name, "执行任务"),
            "model": model_for_agent(name, config),
        }
        for name in agent_names
    ]
