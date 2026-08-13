"""``codex-auto`` entry point.

Routes a task through ``classifier``, selects Flash/Pro, then launches the
underlying ``codex`` command with the selected model.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

from classifier import DiffStats, Factor, classify
from config_loader import load_config
from model_selector import select
from memory.context_builder import build_context

from launcher.agent_runner import run_agent_pipeline
from launcher.execution_mode import (
    determine_execution_mode,
    load_roles,
    model_display_name,
)
from launcher.model_runner import RunPlan, build_command, resolve_codex_bin, run


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config.yaml"


# Router flags that consume a following value.
ROUTER_VALUE_FLAGS = {
    "--repo",
    "--diff-file",
    "--codex-bin",
    "--mode",
    "--model-switch",
}

# Router flags that do not consume a value.
ROUTER_BOOL_FLAGS = {
    "--pro",
    "--flash",
    "--auto",
    "--direct",
    "--agent",
    "--yes",
    "--no",
    "--dry-run",
    "--router-json",
}

# codex CLI flags that consume a value. Everything not listed here is passed
# through to codex as a boolean option.
CODEX_VALUE_FLAGS = {
    "-c",
    "--config",
    "-m",
    "--model",
    "--enable",
    "--disable",
    "--remote",
    "--remote-auth-token-env",
    "-i",
    "--image",
    "--local-provider",
    "-p",
    "--profile",
    "-s",
    "--sandbox",
    "-C",
    "--cd",
    "--add-dir",
    "--output-schema",
    "--color",
    "-o",
    "--output-last-message",
    "-a",
    "--ask-for-approval",
}

# Commands that manage Codex itself instead of running an agent task. These are
# always forwarded to the real codex binary and never passed through the router.
CODEX_SUBCOMMANDS = {
    "exec",
    "e",
    "review",
    "login",
    "logout",
    "mcp",
    "mcp-server",
    "app-server",
    "remote-control",
    "app",
    "completion",
    "update",
    "doctor",
    "sandbox",
    "debug",
    "apply",
    "a",
    "resume",
    "archive",
    "delete",
    "unarchive",
    "fork",
    "cloud",
    "exec-server",
    "features",
    "help",
}


@dataclass
class LauncherArgs:
    task_parts: list[str] = field(default_factory=list)
    codex_args: list[str] = field(default_factory=list)
    override: str | None = None
    repo: str | None = None
    diff_file: str | None = None
    yes: bool = False
    no: bool = False
    dry_run: bool = False
    router_json: bool = False
    codex_bin: str | None = None
    mode: str | None = None
    model_switch: str | None = None
    mode_override: str | None = None


def parse_launcher_args(argv: list[str]) -> LauncherArgs:
    """Split argv into router options, codex passthrough args, and task."""
    result = LauncherArgs()
    i = 0

    while i < len(argv):
        arg = argv[i]

        if arg in ROUTER_VALUE_FLAGS:
            if i + 1 >= len(argv):
                raise SystemExit(f"{arg} 需要一个值")
            value = argv[i + 1]
            if arg == "--repo":
                result.repo = value
            elif arg == "--diff-file":
                result.diff_file = value
            elif arg == "--codex-bin":
                result.codex_bin = value
            elif arg == "--mode":
                result.mode = value
            elif arg == "--model-switch":
                result.model_switch = value
            i += 2
            continue

        if arg in ROUTER_BOOL_FLAGS:
            if arg == "--pro":
                result.override = "pro"
            elif arg == "--flash":
                result.override = "flash"
            elif arg == "--auto":
                result.override = None
            elif arg == "--direct":
                result.mode_override = "direct"
            elif arg == "--agent":
                result.mode_override = "agent"
            elif arg == "--yes":
                result.yes = True
            elif arg == "--no":
                result.no = True
            elif arg == "--dry-run":
                result.dry_run = True
            elif arg == "--router-json":
                result.router_json = True
            i += 1
            continue

        if arg == "-" or not arg.startswith("-"):
            result.task_parts.append(arg)
            i += 1
            continue

        # Unknown option: pass it through to codex.
        result.codex_args.append(arg)
        if arg in CODEX_VALUE_FLAGS and i + 1 < len(argv):
            result.codex_args.append(argv[i + 1])
            i += 1
        i += 1

    return result


def should_route(argv: list[str]) -> bool:
    """Return True when argv looks like ``codex [options] <task>``.

    Subcommands and option-only invocations (``--help``, ``--version``,
    ``--add-dir ...``) are handled by the real codex binary directly.
    """
    if not argv:
        return False
    if argv[0].lower() in CODEX_SUBCOMMANDS:
        return False
    try:
        parsed = parse_launcher_args(argv)
    except SystemExit:
        return False
    return bool(parsed.task_parts)


def run_real_passthrough(raw_args: list[str], config: dict) -> int:
    """Forward args unchanged to the real codex binary."""
    codex_bin = resolve_codex_bin(config["launcher"]["codex_bin"])
    plan = RunPlan(command=[codex_bin] + raw_args, env={})
    return run(plan)


def read_diff_stats(repo: str | None, diff_file: str | None) -> DiffStats:
    if diff_file:
        try:
            text = Path(diff_file).read_text(encoding="utf-8")
        except OSError as exc:
            raise SystemExit(f"无法读取 diff 文件: {exc}") from exc
        files = lines = 0
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

    if repo:
        from router import collect_git_diff

        return collect_git_diff(repo)

    return DiffStats()


def format_direct_log(task: str, classification, selection, mode: str) -> str:
    mode_label = "Direct Mode" if mode == "direct" else "Enhanced Direct Mode"
    lines = [
        "=====================",
        "Codex Router",
        "",
        "任务:",
        task,
        "",
        "复杂度:",
        f"{classification.score}/100",
        "",
        "Execution Mode:",
        mode_label,
    ]

    if mode == "enhanced":
        lines += [
            "",
            "任务理解:",
            task,
            "",
            "修改计划:",
            "- 先阅读相关代码与项目结构",
            "- 保持最小化改动",
        ]
        if classification.reasons:
            lines.append("- 评分因素: " + "；".join(classification.reasons))
        lines += ["", "风险:", "- 中等复杂度，先计划后执行"]

    lines += [
        "",
        "选择模型:",
        f"{selection.tier.title()} ({selection.model_name})",
        "",
        "原因:",
    ]
    lines += [f"- {reason}" for reason in classification.reasons]
    lines += [f"- {selection.reason}", "", "启动Codex...", "====================="]
    return "\n".join(lines)


def format_agent_log(task: str, classification, config) -> str:
    roles = load_roles(config)
    lines = [
        "=====================",
        "Codex Router",
        "",
        "任务:",
        task,
        "",
        "复杂度:",
        f"{classification.score}/100",
        "",
        "Execution Mode:",
        "Agent Mode",
        "",
        "Supervisor:",
        "Enabled",
        "",
        "Agents:",
    ]
    for role in roles:
        lines.append(f"{role.name.title()}: {model_display_name(role.model_tier, config)}")
    lines.append("=====================")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    config = load_config(CONFIG_PATH)

    entry_mode = False
    if argv and argv[0] == "--entry":
        entry_mode = True
        argv = argv[1:]
        if not should_route(argv):
            return run_real_passthrough(argv, config)

    args = parse_launcher_args(argv)
    threshold = config["threshold"]
    launcher_cfg = config["launcher"]

    if args.codex_bin:
        launcher_cfg["codex_bin"] = args.codex_bin
    if args.mode:
        launcher_cfg["mode"] = args.mode
    if args.model_switch:
        launcher_cfg["model_switch"] = args.model_switch

    task_parts = list(args.task_parts)
    if task_parts and task_parts[0] == "-":
        stdin_text = sys.stdin.read()
        task_parts = [stdin_text] + task_parts[1:]

    task = " ".join(task_parts).strip()
    if not task:
        print("错误：没有提供任务文本。", file=sys.stderr)
        return 2

    # Text-level /model command is a fallback when no --flash/--pro is given.
    from router import parse_model_command

    text_override, task = parse_model_command(task)
    if args.override is None and text_override:
        args.override = text_override

    context_start = args.repo if args.repo else None
    project_context = build_context(start=context_start)

    diff = read_diff_stats(args.repo, args.diff_file)
    classification = classify(task, diff, threshold_pro=int(threshold["pro_score"]))
    if project_context.score_bonus:
        classification.score = max(
            0, min(100, classification.score + project_context.score_bonus)
        )
        classification.factors.append(
            Factor(
                "项目上下文",
                project_context.score_bonus,
                project_context.bonus_reason,
            )
        )

    selection = select(classification.score, config, args.override)
    execution = determine_execution_mode(
        classification.score,
        config,
        args.mode_override,
    )

    if not args.router_json:
        print(project_context.to_display())
        print()

    if execution == "agent":
        roles = load_roles(config)
        if args.router_json:
            print(
                json.dumps(
                    {
                        "task": task,
                        "complexity": classification.score,
                        "mode": "agent",
                        "project": project_context.project_name,
                        "tech_stack": project_context.tech_stack,
                        "agents": [
                            {
                                "role": role.name,
                                "model": model_display_name(role.model_tier, config),
                            }
                            for role in roles
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
        else:
            print(format_agent_log(task, classification, config))

        agents_enabled = bool(config.get("agents", {}).get("enabled", True))
        if args.dry_run or not agents_enabled:
            if not agents_enabled and not args.dry_run:
                print("\nAgent 模式已禁用，仅输出编排预览。")
            return run_agent_pipeline(
                task,
                config,
                dry_run=True,
                project_context=project_context.to_markdown(),
            )
        return run_agent_pipeline(
            task,
            config,
            dry_run=False,
            project_context=project_context.to_markdown(),
        )

    if args.router_json:
        print(
            json.dumps(
                {
                    "task": task,
                    "complexity": classification.score,
                    "tier": classification.tier,
                    "mode": execution,
                    "project": project_context.project_name,
                    "tech_stack": project_context.tech_stack,
                    "model": {
                        "tier": selection.tier,
                        "provider": selection.provider,
                        "model_name": selection.model_name,
                        "mode": selection.mode,
                    },
                    "reasons": classification.reasons + [selection.reason],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print(format_direct_log(task, classification, selection, execution))

    # Safety gate before actually spending tokens on Pro.
    if (
        selection.tier == "pro"
        and classification.estimated_tokens
        > int(threshold["pro_token_warning"])
    ):
        if args.yes:
            print("已自动确认使用 Pro。")
        elif args.no:
            print("已取消：--no 拒绝 Pro 执行。")
            return 1
        else:
            print(
                f"\n检测到复杂任务，预计使用 Pro（预估 "
                f"{classification.estimated_tokens} tokens > 阈值 "
                f"{threshold['pro_token_warning']}）"
            )
            answer = input("是否继续？(yes/no) > ").strip().lower()
            if answer not in {"yes", "y"}:
                print("已取消 Pro 执行。")
                return 1

    codex_prompt = project_context.to_markdown() + "\n\n# 用户任务\n" + task
    plan = build_command(selection, codex_prompt, args.codex_args, config)
    return run(plan, dry_run=args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
