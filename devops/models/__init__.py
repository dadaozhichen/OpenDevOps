"""Unified entry for multiple model providers."""

from __future__ import annotations

from typing import Optional

from devops.config import ModelConfig, list_providers
from devops.models.base import BaseChatModel
from devops.models.openai import OpenAIChatModel
from devops.models.zhipuai import ZhipuAIChatModel

# deepseek / moonshot use OpenAI-compatible APIs
_OPENAI_COMPAT = {"openai", "deepseek", "moonshot"}


def create_chat_model(config: ModelConfig) -> BaseChatModel:
  provider = config.provider.lower()
  if provider in _OPENAI_COMPAT:
    return OpenAIChatModel(config)
  if provider == "zhipuai":
    return ZhipuAIChatModel(config)
  raise ValueError(
    f"Unsupported provider: {provider}. Choose: {', '.join(list_providers())}"
  )


def get_chat_model(
  *,
  provider: Optional[str] = None,
  api_key: Optional[str] = None,
  model: Optional[str] = None,
  base_url: Optional[str] = None,
) -> BaseChatModel:
  from devops.config import load_config

  config = load_config(
    provider=provider,
    api_key=api_key,
    model=model,
    base_url=base_url,
  )
  return create_chat_model(config)


__all__ = [
  "BaseChatModel",
  "OpenAIChatModel",
  "ZhipuAIChatModel",
  "create_chat_model",
  "get_chat_model",
  "list_providers",
]
