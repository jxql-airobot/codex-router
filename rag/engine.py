"""Query a project KnowledgeIndex."""

from __future__ import annotations

from dataclasses import dataclass

from knowledge.indexer import KnowledgeIndex
from vector_store.store import Document


@dataclass
class RetrievedChunk:
    document: Document
    score: float


class RagEngine:
    def __init__(self, index: KnowledgeIndex) -> None:
        self.index = index

    def retrieve(self, question: str, top_k: int = 5) -> list[RetrievedChunk]:
        results = self.index.store.search(question, top_k=top_k)
        return [
            RetrievedChunk(document=document, score=score)
            for document, score in results
            if score > 0
        ]

    def evidence_markdown(self, question: str, top_k: int = 5) -> str:
        lines = [f"# Question\n{question}\n", "# Evidence"]
        for result in self.retrieve(question, top_k=top_k):
            source = result.document.metadata.get("source", "-")
            lines.append(
                f"\n- [{source}] score={result.score:.3f}\n{result.document.text.strip()[:800]}"
            )
        return "\n".join(lines)
