"""Zhipu AI (GLM) model client."""

from __future__ import annotations

from devops.config import ModelConfig
from devops.models.base import BaseChatModel


class ZhipuAIChatModel(BaseChatModel):
    def __init__(self, config: ModelConfig) -> None:
        super().__init__(config)
        try:
            from zhipuai import ZhipuAI
        except ImportError as exc:
            raise ImportError("Zhipu AI requires: pip install zhipuai") from exc

        self._client = ZhipuAI(api_key=config.api_key)

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
