"""多模型提供商统一入口。"""

from __future__ import annotations

from devops.config import ModelConfig, list_providers
from devops.models.base import BaseChatModel
from devops.models.openai import OpenAIChatModel
from devops.models.zhipuai import ZhipuAIChatModel

# deepseek / moonshot 使用 OpenAI 兼容协议
_OPENAI_COMPAT = {"openai", "deepseek", "moonshot"}


def create_chat_model(config: ModelConfig) -> BaseChatModel:
  provider = config.provider.lower()
  if provider in _OPENAI_COMPAT:
    return OpenAIChatModel(config)
  if provider == "zhipuai":
    return ZhipuAIChatModel(config)
  raise ValueError(
    f"不支持的提供商: {provider}，可选: {', '.join(list_providers())}"
  )


def get_chat_model(
  *,
  provider: str | None = None,
  api_key: str | None = None,
  model: str | None = None,
  base_url: str | None = None,
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
