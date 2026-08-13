"""Capability-based agent selection."""

from __future__ import annotations

from typing import Any


CAPABILITIES: dict[str, list[str]] = {
    "ArchitectAgent": ["架构", "设计", "系统", "技术选型"],
    "RobotAgent": ["ros2", "机器人", "导航", "communication", "robot"],
    "RAGAgent": ["知识", "文档", "rag", "记忆", "documentation", "knowledge"],
    "CoderAgent": ["实现", "代码", "开发", "修改", "重构"],
    "TesterAgent": ["测试", "验证", "报错"],
    "ResearchAgent": ["论文", "实验", "调研", "paper", "research"],
    "PLC_Agent": ["plc", "automation", "工业", "industrial"],
}


def select_agents(analysis: dict[str, Any]) -> list[str]:
    text = f"{analysis.get('type','')} {analysis.get('domain','')}".lower()
    selected: list[str] = []
    for agent, keywords in CAPABILITIES.items():
        if any(keyword.lower() in text for keyword in keywords):
            selected.append(agent)

    level = analysis.get("planning_level", 0)
    if level <= 0:
        return ["CoderAgent"]
    if level == 1:
        return list(dict.fromkeys(["RAGAgent", "CoderAgent"]))
    if "ArchitectAgent" not in selected:
        selected.insert(0, "ArchitectAgent")
    if "CoderAgent" not in selected:
        selected.append("CoderAgent")
    if "TesterAgent" not in selected:
        selected.append("TesterAgent")
    return list(dict.fromkeys(selected))
