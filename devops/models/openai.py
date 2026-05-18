"""OpenAI 及兼容 OpenAI 协议的服务（DeepSeek、Moonshot、本地 Ollama 等）。"""

from __future__ import annotations

from typing import Any

from devops.config import ModelConfig
from devops.models.base import BaseChatModel


class OpenAIChatModel(BaseChatModel):
    def __init__(self, config: ModelConfig) -> None:
        super().__init__(config)
        from openai import OpenAI

        kwargs: dict[str, Any] = {"api_key": config.api_key}
        if config.base_url:
            kwargs["base_url"] = config.base_url.rstrip("/")
        self._client = OpenAI(**kwargs)

    def chat(self, system: str, user: str, *, temperature: float = 0.2) -> str:
        response = self._client.chat.completions.create(
            model=self.config.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=temperature,
        )
        return (response.choices[0].message.content or "").strip()
