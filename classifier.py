"""Task complexity classifier for the Codex model router.

The classifier turns a natural-language task (and optional git diff stats)
into a complexity score between 0 and 100, plus a list of human-readable
reasons. The score is intentionally transparent and deterministic so it is
easy to audit and tune.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


BASE_SCORE = 20

# Lower-case keys are matched case-insensitively. Chinese terms are matched
# exactly. Each occurrence contributes the weight, capped at two occurrences
# per term so a repeated word does not dominate the score.
PRO_KEYWORDS: dict[str, int] = {
    "架构": 20,
    "设计": 15,
    "重构": 20,
    "系统": 15,
    "优化整体": 20,
    "论文": 25,
    "实验": 20,
    "算法": 20,
    "agent": 15,
    "模型": 15,
    "ros2": 12,
    "导航": 12,
    "规划": 15,
    "闭环": 20,
    "vision-language-action": 25,
    "机器人": 10,
}

SIMPLE_KEYWORDS: dict[str, int] = {
    "修改": -15,
    "添加": -15,
    "增加": -12,
    "删除": -15,
    "格式": -15,
    "注释": -15,
    "测试": -12,
    "修复": -12,
    "配置": -10,
    "查看": -12,
    "日志": -10,
    "文档": -12,
    "readme": -12,
    "bug": -12,
}

FILE_EXTENSIONS = (
    r"py|cpp|cc|cxx|h|hpp|rs|ts|tsx|js|jsx|java|go|rb|php|yaml|yml|json|toml|md|"
    r"sh|bat|ps1|cfg|ini|cmake|txt"
)


@dataclass
class Factor:
    """A single scoring factor shown in the execution log."""

    name: str
    points: int
    detail: str


@dataclass
class DiffStats:
    """Aggregated scope information extracted from ``git diff``."""

    files_changed: int = 0
    lines_changed: int = 0

    @property
    def available(self) -> bool:
        return self.files_changed > 0 or self.lines_changed > 0


@dataclass
class Classification:
    """Result of classifying a task."""

    score: int
    factors: list[Factor] = field(default_factory=list)
    estimated_tokens: int = 0

    @property
    def tier(self) -> str:
        if self.score < 40:
            return "simple"
        if self.score < 70:
            return "medium"
        return "complex"

    @property
    def reasons(self) -> list[str]:
        return [f"{f.name}: {f.detail} ({f.points:+d})" for f in self.factors]


def _count_keywords(text: str, keywords: dict[str, int]) -> tuple[int, list[str]]:
    """Count keyword contributions and return (total, matched detail list)."""
    total = 0
    matches: list[str] = []
    lower = text.lower()

    for term, weight in keywords.items():
        haystack = lower if term.isascii() else text
        count = haystack.count(term if term.isascii() else term.lower())
        if count:
            capped = min(count, 2)
            total += weight * capped
            matches.append(f"{term}×{count}")

    return total, matches


def _detect_file_hint(text: str) -> tuple[int | None, list[str]]:
    """Return (file_count_hint, detected_file_paths)."""
    explicit = re.search(r"(\d+)\s*(?:个)?文件", text)
    paths = re.findall(
        rf"[\w./\\-]+\.(?:{FILE_EXTENSIONS})", text, flags=re.IGNORECASE
    )
    unique_paths = sorted({p.strip() for p in paths})

    count: int | None = int(explicit.group(1)) if explicit else None
    if count is None and unique_paths:
        count = len(unique_paths)

    multi = bool(
        re.search(r"多文件|整个仓库|整个项目|整个代码库|大规模", text)
    )
    if multi and (count is None or count < 10):
        count = 10

    return count, unique_paths


def _detect_line_hint(text: str) -> int | None:
    match = re.search(r"(\d+)\s*行", text)
    return int(match.group(1)) if match else None


def estimate_tokens(text: str, diff: DiffStats | None = None) -> int:
    """Rough input-token estimate used only for the Pro safety warning."""
    words = len(re.findall(r"\S+", text))
    text_tokens = int(words * 1.3)
    diff_tokens = int((diff.lines_changed if diff else 0) * 1.5)
    return max(1, text_tokens + diff_tokens)


def classify(
    text: str,
    diff: DiffStats | None = None,
    threshold_pro: int = 70,
) -> Classification:
    """Classify a task into a 0-100 complexity score.

    ``threshold_pro`` is accepted for callers that need to validate the
    boundary, but the model selection itself is handled by
    :mod:`model_selector`.
    """
    diff = diff or DiffStats()
    factors: list[Factor] = []
    score = BASE_SCORE

    # 1. Keyword signals.
    pro_points, pro_matches = _count_keywords(text, PRO_KEYWORDS)
    simple_points, simple_matches = _count_keywords(text, SIMPLE_KEYWORDS)
    score += pro_points + simple_points

    if pro_matches:
        factors.append(Factor("复杂关键词", pro_points, "、".join(pro_matches)))
    if simple_matches:
        factors.append(
            Factor("简单关键词", simple_points, "、".join(simple_matches))
        )

    # 2. File-count signal.
    file_count, detected_paths = _detect_file_hint(text)
    if file_count is not None:
        if file_count == 1:
            file_points = -10
        elif file_count <= 4:
            file_points = 10
        elif file_count <= 9:
            file_points = 25
        else:
            file_points = 40
        score += file_points

        detail = f"预估 {file_count} 个文件"
        if detected_paths:
            detail += "（检测到文件路径）"
        factors.append(Factor("文件数量", file_points, detail))

    # 3. Line-count signal from the task text.
    line_hint = _detect_line_hint(text)
    if line_hint is not None:
        if line_hint < 100:
            line_points = -10
        elif line_hint <= 500:
            line_points = 10
        else:
            line_points = 30
        score += line_points
        factors.append(Factor("文本行数提示", line_points, f"约 {line_hint} 行"))

    # 4. Git diff scope signal (strongest evidence when available).
    if diff.available:
        if diff.lines_changed < 100:
            diff_points = -10
        elif diff.lines_changed <= 500:
            diff_points = 10
        else:
            diff_points = 30

        if diff.files_changed == 1:
            diff_points -= 10
        elif diff.files_changed >= 10:
            diff_points += 20

        score += diff_points
        factors.append(
            Factor(
                "Git diff 范围",
                diff_points,
                f"{diff.files_changed} 个文件 / {diff.lines_changed} 行改动",
            )
        )

    score = max(0, min(100, score))
    return Classification(
        score=score,
        factors=factors,
        estimated_tokens=estimate_tokens(text, diff),
    )
