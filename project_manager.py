"""CLI for the multi-project registry."""

from __future__ import annotations

import argparse
import json

from project_manager.manager import ProjectManager


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Multi-project manager")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list", help="list registered projects")
    reg = sub.add_parser("register", help="register a project")
    reg.add_argument("path")
    load = sub.add_parser("load", help="load memory and RAG for a project")
    load.add_argument("path")
    args = parser.parse_args(argv)

    manager = ProjectManager()
    if args.command == "list":
        print(json.dumps([item.__dict__ for item in manager.list()], ensure_ascii=False, indent=2))
    elif args.command == "register":
        record = manager.register(args.path)
        print(json.dumps(record.__dict__, ensure_ascii=False, indent=2))
    elif args.command == "load":
        snapshot = manager.load(args.path)
        print(
            json.dumps(
                {
                    "project": snapshot["project"],
                    "tech_stack": snapshot["tech_stack"],
                    "rag_documents": len(snapshot["rag"].store),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
