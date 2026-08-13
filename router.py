"""Command-line entry point for the Codex AI model router.

Examples:
    python router.py "修复Python报错"
    python router.py "设计ROS2机器人Agent架构" --repo /path/to/robot
    python router.py /model pro "重构ROS2通信层"
    echo "增加一个测试" | python router.py -
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

from classifier import DiffStats, classify
from model_selector import ModelInfo, load_config, select


ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "config.yaml"


def parse_model_command(text: str) -> tuple[str | None, str]:
    """Extract a leading ``/model ...`` command and return (override, task)."""
    match = re.match(r"^\s*/model\s+(flash|pro|auto)\b\s*", text, re.IGNORECASE)
    if not match:
        return None, text
    return match.group(1).lower(), text[match.end() :].strip()


def collect_git_diff(repo: str | Path | None) -> DiffStats:
    """Collect uncommitted/staged diff stats from ``repo``."""
    if not repo:
        return DiffStats()

    repo_path = Path(repo)
    commands = [
        ["git", "-C", str(repo_path), "diff", "HEAD", "--numstat"],
        ["git", "-C", str(repo_path), "diff", "--numstat"],
    ]
    for cmd in commands:
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                return parse_numstat(result.stdout)
        except FileNotFoundError:
            return DiffStats()

    return DiffStats()


def parse_numstat(text: str) -> DiffStats:
    files = 0
    lines = 0
    for raw in text.splitlines():
        parts = raw.split("\t")
        if len(parts) != 3:
            continue
        try:
            added = int(parts[0]) if parts[0] != "-" else 0
            deleted = int(parts[1]) if parts[1] != "-" else 0
        except ValueError:
            continue
        files += 1
        lines += added + deleted
    return DiffStats(files_changed=files, lines_changed=lines)


def read_diff_file(path: str | Path) -> DiffStats:
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        raise SystemExit(f"无法读取 diff 文件: {exc}") from exc
    return parse_numstat(text)


def format_log(task: str, classification, model: ModelInfo) -> str:
    lines = [
        "Task Router:",
        "",
        f"任务:\n{task}",
        "",
        f"复杂度:\n{classification.score}/100",
        "",
        "选择模型:",
        f"{model.model_name} ({model.provider})",
        "",
        "原因:",
    ]
    if classification.reasons:
        lines.extend(f"- {reason}" for reason in classification.reasons)
        lines.append(f"- {model.reason}")
    else:
        lines.append(f"- {model.reason}")
    return "\n".join(lines)


def confirm_pro(estimated_tokens: int, warning_threshold: int) -> bool:
    print(
        f"\n检测到复杂任务，预计使用 Pro（预估 {estimated_tokens} tokens > "
        f"阈值 {warning_threshold}）"
    )
    print("是否继续？(yes/no)")
    while True:
        answer = input("> ").strip().lower()
        if answer in {"yes", "y"}:
            return True
        if answer in {"no", "n"}:
            return False
        print("请输入 yes 或 no")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Codex AI Model Router：根据任务复杂度选择 Flash / Pro",
    )
    parser.add_argument(
        "task",
        nargs="*",
        help="用户任务文本；使用 '-' 从 stdin 读取",
    )
    parser.add_argument("--repo", help="目标仓库路径，用于分析 git diff")
    parser.add_argument("--diff-file", help="git diff --numstat 输出文件")
    parser.add_argument(
        "--model",
        choices=["auto", "flash", "pro"],
        help="覆盖模型选择（等价于任务前的 /model 命令）",
    )
    parser.add_argument("--yes", action="store_true", help="自动确认 Pro 安全提示")
    parser.add_argument("--no", action="store_true", help="自动拒绝 Pro 安全提示")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    task_parts = list(args.task)
    if task_parts and task_parts[0] == "-":
        stdin_text = sys.stdin.read()
        task_parts = [stdin_text] + task_parts[1:]

    task = " ".join(task_parts).strip()
    if not task:
        print("错误：没有提供任务文本。", file=sys.stderr)
        build_parser().print_help(sys.stderr)
        return 2

    override_from_text, task = parse_model_command(task)
    if not task:
        print("错误：/model 命令后没有任务内容。", file=sys.stderr)
        return 2

    override = args.model if args.model and args.model != "auto" else override_from_text

    config = load_config(CONFIG_PATH)
    threshold = config["threshold"]

    if args.diff_file:
        diff = read_diff_file(args.diff_file)
    else:
        diff = collect_git_diff(args.repo)

    classification = classify(task, diff, threshold_pro=int(threshold["pro_score"]))
    model = select(classification.score, config, override)

    payload = {
        "task": task,
        "complexity": classification.score,
        "tier": classification.tier,
        "estimated_tokens": classification.estimated_tokens,
        "model": {
            "tier": model.tier,
            "provider": model.provider,
            "model_name": model.model_name,
            "mode": model.mode,
        },
        "reasons": classification.reasons + [model.reason],
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(format_log(task, classification, model))

    # Safety gate only applies to automatic/forced Pro runs with a large scope.
    if (
        model.tier == "pro"
        and classification.estimated_tokens
        > int(threshold["pro_token_warning"])
    ):
        if args.yes:
            print("\n已自动确认使用 Pro。")
        elif args.no:
            print("\n已取消：--no 拒绝 Pro 执行。")
            return 1
        elif not confirm_pro(
            classification.estimated_tokens, int(threshold["pro_token_warning"])
        ):
            print("\n已取消 Pro 执行。")
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
