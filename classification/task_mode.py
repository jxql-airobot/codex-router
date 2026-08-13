"""Fast path / complex path task-mode routing.

Decides whether a user input can skip the full Supervisor/Agent pipeline and
route directly through the active provider (``fast``) or needs the full
pipeline (``complex``). Pure and deterministic: no network, no LLM, and never
changes the active model.
"""

from __future__ import annotations

from typing import Any

# Force-complex: unambiguous code / project / architecture terms. Checked
# first so a greeting that also contains "修改代码" still routes complex.
STRONG_COMPLEX = [
    # Chinese actions
    "修改", "实现", "开发", "设计", "重构", "添加", "增加", "删除",
    "部署", "优化", "构建", "集成", "编写", "创建", "修复", "调试",
    "运行", "项目", "架构", "系统设计", "技术选型",
    "运行测试", "添加测试", "写测试", "测试失败", "测试代码",
    # English actions / domain terms
    "modify", "implement", "develop", "design", "refactor", "add",
    "remove", "delete", "deploy", "optimize", "build", "integrate",
    "write", "create", "fix", "debug", "run", "project", "architecture",
    "ros", "agent", "code", "feature", "bug", "pytest", "unittest",
    "colcon", "npm test",
]

# File-operation signals.
FILE_SIGNALS = [
    ".py", ".yaml", ".yml", ".json", ".toml", ".md", ".txt",
    ".cpp", ".hpp", ".c", ".h", ".rs", ".go", ".js", ".ts", ".java",
    "文件", "读取", "写入", "readme", "src/", "tests/", "config",
    "commit",
]

# Multi-step / long task signals.
MULTI_STEP_SIGNALS = [
    "步骤", "第一步", "第二步", "第三步", "第四步", "第五步",
    "首先", "然后", "最后", "完成以下", "以下功能", "以下任务",
    "多个", "多文件", "1.", "2.", "3.", "4.", "5.",
    "step", "first", "then", "finally",
]

# Fast intents: short questions / chitchat that should never route complex.
FAST_INTENTS = [
    "你好", "您好", "谢谢", "感谢", "再见", "拜拜",
    "解释", "是什么", "为什么", "怎么", "如何", "什么意思",
    "查看版本", "版本", "输出", "测试", "帮助",
    "hi", "hello", "hey", "thanks", "thank", "bye",
    "explain", "what is", "why", "how", "version", "help",
    "output", "test",
]

FAST_MAX_CHARS = 50


def classify_mode(task: str) -> dict[str, Any]:
    """Return ``{'mode', 'reason', 'confidence'}`` for a user input."""
    text = (task or "").strip()
    lowered = text.lower()

    if not text:
        return {"mode": "fast", "reason": "empty_input", "confidence": 0.99}

    for keyword in STRONG_COMPLEX:
        if keyword in lowered:
            return {"mode": "complex", "reason": "code_change", "confidence": 0.9}

    for signal in FILE_SIGNALS:
        if signal in lowered:
            return {"mode": "complex", "reason": "file_operation", "confidence": 0.9}

    for signal in MULTI_STEP_SIGNALS:
        if signal in lowered:
            return {"mode": "complex", "reason": "multi_step", "confidence": 0.85}

    for keyword in FAST_INTENTS:
        if keyword in lowered:
            return {"mode": "fast", "reason": "simple_question", "confidence": 0.95}

    if len(text) <= FAST_MAX_CHARS:
        return {"mode": "fast", "reason": "short_input", "confidence": 0.7}
    return {"mode": "complex", "reason": "long_input", "confidence": 0.6}
