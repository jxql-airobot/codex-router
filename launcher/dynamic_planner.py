"""Plan a dynamic agent team based on task domain."""

from __future__ import annotations

from typing import Any

from launcher.execution_mode import AgentRole


DOMAIN_TEAMS: dict[str, list[dict[str, str]]] = {
    "software": [
        {"name": "requirement", "model": "pro", "sandbox": "read-only", "instruction": "分析需求并输出需求清单"},
        {"name": "architecture", "model": "pro", "sandbox": "read-only", "instruction": "设计系统架构与技术方案"},
        {"name": "backend", "model": "flash", "sandbox": "workspace-write", "instruction": "实现后端接口与数据层"},
        {"name": "frontend", "model": "flash", "sandbox": "workspace-write", "instruction": "实现前端界面"},
        {"name": "testing", "model": "flash", "sandbox": "workspace-write", "instruction": "编写并运行测试"},
        {"name": "reviewer", "model": "pro", "sandbox": "read-only", "instruction": "审查代码与架构"},
    ],
    "data": [
        {"name": "research", "model": "pro", "sandbox": "read-only", "instruction": "调研数据来源与分析目标"},
        {"name": "data", "model": "flash", "sandbox": "workspace-write", "instruction": "数据清洗与预处理"},
        {"name": "python", "model": "flash", "sandbox": "workspace-write", "instruction": "编写分析脚本"},
        {"name": "visualization", "model": "flash", "sandbox": "workspace-write", "instruction": "生成可视化图表"},
        {"name": "reviewer", "model": "pro", "sandbox": "read-only", "instruction": "审查分析结论"},
    ],
    "paper": [
        {"name": "research", "model": "pro", "sandbox": "read-only", "instruction": "文献调研与背景整理"},
        {"name": "experiment", "model": "pro", "sandbox": "workspace-write", "instruction": "设计并运行实验"},
        {"name": "writer", "model": "flash", "sandbox": "workspace-write", "instruction": "撰写论文"},
        {"name": "reviewer", "model": "pro", "sandbox": "read-only", "instruction": "审阅论文"},
    ],
    "ros2": [
        {"name": "planner", "model": "pro", "sandbox": "read-only", "instruction": "规划 ROS2 系统架构"},
        {"name": "coder", "model": "flash", "sandbox": "workspace-write", "instruction": "实现 ROS2 节点与通信"},
        {"name": "tester", "model": "flash", "sandbox": "workspace-write", "instruction": "运行仿真与测试"},
        {"name": "reviewer", "model": "pro", "sandbox": "read-only", "instruction": "审查 ROS2 架构"},
    ],
}


def detect_domain(task: str) -> str:
    text = task.lower()
    if any(word in text for word in ("数据", "分析", "可视化", "报表", "统计")):
        return "data"
    if any(word in text for word in ("论文", "实验", "文献", "写作", "期刊")):
        return "paper"
    if any(word in text for word in ("ros2", "机器人", "导航", "gazebo", "节点", "话题")):
        return "ros2"
    return "software"


def plan_roles(task: str, config: dict[str, Any] | None = None) -> list[AgentRole]:
    domain = detect_domain(task)
    team = DOMAIN_TEAMS.get(domain, DOMAIN_TEAMS["software"])
    return [
        AgentRole(
            name=item["name"],
            model_tier=item["model"],
            sandbox=item["sandbox"],
            instructions=item["instruction"],
        )
        for item in team
    ]
