"""Provider interface decoupled from agents."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Iterator


class LLMProvider(ABC):
    name: str = "base"

    @abstractmethod
    def chat(self, messages: list[dict[str, str]]) -> str:
        raise NotImplementedError

    @abstractmethod
    def generate(self, prompt: str) -> str:
        raise NotImplementedError

    def stream(self, prompt: str) -> Iterator[str]:
        yield self.generate(prompt)
