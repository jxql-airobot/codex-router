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
from classification.task_classifier import classify_task
from config_loader import load_config
from integration.session_manager import SessionManager
from model_selector import select
from memory.context_builder import build_context

from launcher.agent_runner import run_agent_pipeline
from launcher.dynamic_planner import plan_roles
from launcher.execution_mode import (
    determine_execution_mode,
    load_roles,
    model_display_name,
)
from launcher.model_runner import RunPlan, build_command, resolve_codex_bin, run


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config.yaml"
_AUTO_SESSIONS = SessionManager()


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
    "--git",
    "--workflow",
    "--workflow-status",
    "--usage",
    "--detail",
    "--dashboard",
    "--usage-cn",
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
    git: bool = False
    workflow: bool = False
    workflow_status: bool = False
    agent_name: str | None = None
    usage: bool = False
    detail: bool = False
    dashboard: bool = False
    usage_cn: bool = False


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

        if arg == "--agent":
            if i + 1 < len(argv) and not argv[i + 1].startswith("-"):
                result.agent_name = argv[i + 1]
                i += 2
            else:
                result.mode_override = "agent"
                i += 1
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
            elif arg == "--git":
                result.git = True
            elif arg == "--workflow":
                result.workflow = True
            elif arg == "--workflow-status":
                result.workflow_status = True
            elif arg == "--usage":
                result.usage = True
            elif arg == "--detail":
                result.detail = True
            elif arg == "--dashboard":
                result.dashboard = True
            elif arg == "--usage-cn":
                result.usage_cn = True
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


def format_agent_log(task: str, classification, config, roles=None) -> str:
    roles = roles if roles is not None else load_roles(config)
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


def _maybe_git_report(args: LauncherArgs, exit_code: int, repo: str | None) -> None:
    if not (args.git and exit_code == 0 and not args.dry_run):
        return

    from git_manager.commit_generator import generate_commit_message
    from git_manager.diff_analyzer import analyze_diff
    from git_manager.scanner import scan_git

    diff = analyze_diff(repo)
    info = scan_git(repo)
    message = generate_commit_message(diff)
    print("\n[Git Lifecycle]")
    print(f"Branch: {info.branch or '-'}")
    print(f"Changes: {diff.total}")
    print(f"Suggested commit: {message}")


def _auto_record_usage(auto_plan: dict, project: str, classification, exit_code: int) -> None:
    from usage.models import UsageRecord
    from usage.tracker import UsageTracker

    tracker = UsageTracker()
    tracker.track(
        UsageRecord(
            project=project,
            agent=", ".join(auto_plan.get("recommended_agents", [])),
            provider="auto",
            model="",
            input_tokens=classification.estimated_tokens,
            output_tokens=0,
            total_tokens=classification.estimated_tokens,
            task_id=auto_plan.get("session_id", ""),
            task_type=auto_plan.get("type", ""),
            workflow=auto_plan.get("recommended_workflow", ""),
            success=exit_code == 0,
        )
    )
    tracker.close()


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

    if args.workflow_status:
        from orchestrator.workflow import load_workflow
        from workflow import WORKFLOW_PATH, build_manager

        workflow = load_workflow(WORKFLOW_PATH)
        print("workflow:", " -> ".join(workflow.steps))
        print("agents:", build_manager().names())
        return 0

    if args.usage:
        from usage_cli import render

        print(render(detail=args.detail))
        return 0

    if args.usage_cn:
        from usage_cli import render_cn

        print(render_cn(detail=args.detail))
        return 0

    if args.dashboard:
        from analytics.statistics import chinese_number, overview
        from pathlib import Path

        data = overview()
        print("AI开发生产力中心")
        print(f"今日Token: {chinese_number(data['total_tokens'])}")
        print(f"成本: ¥{data['cost']:.2f}")
        print(
            "Dashboard 前端:",
            Path(__file__).resolve().parents[1] / "dashboard" / "frontend" / "index.html",
        )
        return 0

    task_parts = list(args.task_parts)
    if task_parts and task_parts[0] == "-":
        stdin_text = sys.stdin.read()
        task_parts = [stdin_text] + task_parts[1:]

    task = " ".join(task_parts).strip()
    if not task:
        print("错误：没有提供任务文本。", file=sys.stderr)
        return 2

    if args.workflow or args.agent_name:
        from memory.context_builder import build_context
        from workflow import build_manager, run_workflow

        context_root = args.repo if args.repo else None
        project_context = build_context(start=context_root)
        if args.agent_name:
            agent = build_manager().get(args.agent_name)
            result = agent.execute(
                task,
                {
                    "project_name": project_context.project_name,
                    "tech_stack": project_context.tech_stack,
                    "repo": args.repo,
                },
            )
            print(result.output)
            return 0 if result.success else 1

        run = run_workflow(task, args.repo)
        print(
            json.dumps(
                {
                    "success": run.success,
                    "outputs": run.outputs,
                    "history": run.history,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0 if run.success else 1

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

    auto_plan = classify_task(
        task, {"project_name": project_context.project_name}
    )
    auto_session_id = _AUTO_SESSIONS.start(task, auto_plan).session_id

    if not args.router_json:
        print(project_context.to_display())
        print()
        print("[Auto Plan]")
        print(
            "type={} workflow={} agents={}".format(
                auto_plan["type"],
                auto_plan["recommended_workflow"],
                ", ".join(auto_plan["recommended_agents"]),
            )
        )
        print()

    if execution == "agent":
        dynamic_enabled = bool(config.get("agents", {}).get("dynamic", False))
        roles = plan_roles(task, config) if dynamic_enabled else load_roles(config)
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
            print(format_agent_log(task, classification, config, roles))

        agents_enabled = bool(config.get("agents", {}).get("enabled", True))
        if args.dry_run or not agents_enabled:
            if not agents_enabled and not args.dry_run:
                print("\nAgent 模式已禁用，仅输出编排预览。")
            exit_code = run_agent_pipeline(
                task,
                config,
                dry_run=True,
                project_context=project_context.to_markdown(),
                roles=roles,
            )
            _AUTO_SESSIONS.finish(
                auto_session_id,
                "success" if exit_code == 0 else "failed",
                tokens=classification.estimated_tokens,
            )
            _auto_record_usage(auto_plan, project_context.project_name, classification, exit_code)
            _maybe_git_report(args, exit_code, context_start)
            return exit_code
        exit_code = run_agent_pipeline(
            task,
            config,
            dry_run=False,
            project_context=project_context.to_markdown(),
            roles=roles,
        )
        _AUTO_SESSIONS.finish(
            auto_session_id,
            "success" if exit_code == 0 else "failed",
            tokens=classification.estimated_tokens,
        )
        _auto_record_usage(auto_plan, project_context.project_name, classification, exit_code)
        _maybe_git_report(args, exit_code, context_start)
        return exit_code

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
    exit_code = run(plan, dry_run=args.dry_run)
    _AUTO_SESSIONS.finish(
        auto_session_id,
        "success" if exit_code == 0 else "failed",
        tokens=classification.estimated_tokens,
    )
    _auto_record_usage(auto_plan, project_context.project_name, classification, exit_code)
    _maybe_git_report(args, exit_code, context_start)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
