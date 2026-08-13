"""A small dependency-free vector store using the hashing trick."""

from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass, field


@dataclass
class Document:
    id: str
    text: str
    metadata: dict = field(default_factory=dict)
    vector: dict[int, float] = field(default_factory=dict)


def tokenize(text: str) -> list[str]:
    lower = text.lower()
    tokens = re.findall(r"[a-z0-9_]+", lower)
    tokens.extend(ch for ch in text if "\u4e00" <= ch <= "\u9fff")
    # Bigrams add a little phrase sensitivity without extra dependencies.
    words = re.findall(r"[a-z0-9_]+", lower)
    tokens.extend(f"{words[i]}_{words[i + 1]}" for i in range(len(words) - 1))
    return tokens


def text_to_vector(text: str, dim: int = 512) -> dict[int, float]:
    vector: dict[int, float] = {}
    for token in tokenize(text):
        digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
        index = int.from_bytes(digest, "little") % dim
        vector[index] = vector.get(index, 0.0) + 1.0
    return normalize(vector)


def normalize(vector: dict[int, float]) -> dict[int, float]:
    norm = math.sqrt(sum(value * value for value in vector.values()))
    if norm == 0:
        return vector
    return {key: value / norm for key, value in vector.items()}


def cosine_similarity(
    left: dict[int, float],
    right: dict[int, float],
) -> float:
    common = left.keys() & right.keys()
    return sum(left[key] * right[key] for key in common)


class VectorStore:
    def __init__(self, dim: int = 512) -> None:
        self.dim = dim
        self._documents: list[Document] = []

    def add(self, doc_id: str, text: str, metadata: dict | None = None) -> Document:
        document = Document(
            id=doc_id,
            text=text,
            metadata=metadata or {},
            vector=text_to_vector(text, self.dim),
        )
        self._documents.append(document)
        return document

    def search(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[tuple[Document, float]]:
        query_vector = text_to_vector(query, self.dim)
        scored = [
            (document, cosine_similarity(query_vector, document.vector))
            for document in self._documents
        ]
        scored.sort(key=lambda pair: pair[1], reverse=True)
        return scored[:top_k]

    def __len__(self) -> int:
        return len(self._documents)
