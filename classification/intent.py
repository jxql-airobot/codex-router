"""Infer task intent, domain, and recommended workflow."""

from __future__ import annotations


TYPE_KEYWORDS = {
    "development": ["添加功能", "修改代码", "重构", "实现", "开发", "增加", "优化"],
    "architecture": ["设计系统", "架构方案", "技术选型", "架构", "设计"],
    "debug": ["报错", "修复", "测试失败", "bug", "调试", "错误"],
    "documentation": ["readme", "文档", "总结", "注释", "说明"],
    "research": ["论文", "调研", "对比", "文献", "实验"],
}

DOMAIN_KEYWORDS = {
    "robotics": ["ros2", "机器人", "导航", "gazebo", "节点", "话题"],
    "web": ["前端", "后端", "web", "api", "页面"],
    "data": ["数据", "分析", "可视化", "报表"],
    "paper": ["论文", "期刊", "写作"],
}

WORKFLOW_BY_TYPE = {
    "development": "developer",
    "architecture": "architecture",
    "debug": "debug",
    "documentation": "document",
    "research": "research",
}


def classify_intent(task: str) -> dict[str, str]:
    text = task.lower()
    task_type = "development"
    for kind, keywords in TYPE_KEYWORDS.items():
        if any(keyword.lower() in text for keyword in keywords):
            task_type = kind
            break

    domain = "general"
    for name, keywords in DOMAIN_KEYWORDS.items():
        if any(keyword.lower() in text for keyword in keywords):
            domain = name
            break

    return {
        "type": task_type,
        "domain": domain,
        "workflow": WORKFLOW_BY_TYPE[task_type],
    }
