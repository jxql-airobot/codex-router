"""Universal AI Engineering Platform entry point.

This is a thin facade over the modules built in v1.0-v1.9. It keeps the final
architecture visible while delegating real execution to the existing router.
"""

from __future__ import annotations

import argparse
import sys

from config_loader import load_config
from launcher.codex_auto import main as router_main
from pathlib import Path


ARCHITECTURE = """Universal AI Engineering Platform

                    User
                      |
               Supervisor AI
                      |
                Agent Runtime
            Codex / DeepSeek / Claude ...
                      |
               Memory + RAG
                      |
          Git / Test / Report / Release
"""


def status(config: dict) -> str:
    roles = config.get("agent_adapters", {})
    enabled = [name for name, cfg in roles.items() if isinstance(cfg, dict) and cfg.get("enabled")]
    lines = [
        ARCHITECTURE.strip(),
        "",
        "Capabilities:",
        "- Task Router / Project Memory / Execution Modes",
        "- Git Automation Lifecycle",
        "- Project Knowledge RAG",
        "- Agent Adapter Framework",
        "- Dynamic Agent Planner",
        "- Parallel Multi-Agent Collaboration",
        "- Multi Project Management",
        "",
        f"Enabled adapters: {', '.join(enabled) or '-'}",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Universal AI Engineering Platform")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status", help="show platform status")
    run = sub.add_parser("run", help="run a task through the platform")
    run.add_argument("task", nargs="*")
    run.add_argument("--dry-run", action="store_true")
    args, extra = parser.parse_known_args(argv)

    config = load_config(Path(__file__).with_name("config.yaml"))
    if args.command == "status":
        print(status(config))
        return 0

    task = " ".join(args.task).strip()
    if not task:
        print("错误：请提供任务。", file=sys.stderr)
        return 2

    forwarded = list(extra)
    if args.dry_run:
        forwarded.append("--dry-run")
    return router_main(["--entry", *forwarded, task])


if __name__ == "__main__":
    raise SystemExit(main())
