"""大模型调用抽象基类。"""

from __future__ import annotations

from abc import ABC, abstractmethod

from devops.config import ModelConfig


class BaseChatModel(ABC):
    def __init__(self, config: ModelConfig) -> None:
        self.config = config

    @abstractmethod
    def chat(self, system: str, user: str, *, temperature: float = 0.2) -> str:
        raise NotImplementedError
