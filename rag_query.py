"""Index the current project and answer a question with evidence.

Usage:
    python rag_query.py "为什么这个模块这样设计？"
"""

from __future__ import annotations

import argparse
import sys

from knowledge.indexer import index_project
from rag.engine import RagEngine


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Project Knowledge RAG query")
    parser.add_argument("question", nargs="*", help="question to retrieve evidence for")
    parser.add_argument("--repo", help="project path (default: current directory)")
    parser.add_argument("--top", type=int, default=5, help="number of evidence chunks")
    args = parser.parse_args(argv)

    question = " ".join(args.question).strip()
    if not question:
        print("错误：请提供问题。", file=sys.stderr)
        return 2

    index = index_project(args.repo)
    engine = RagEngine(index)
    print(engine.evidence_markdown(question, top_k=args.top))
    print(f"\n[Index] files={index.source_files} commits={index.commit_chunks}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
