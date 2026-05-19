"""User model API configuration (~/.devops/config.json)."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Optional

CONFIG_DIR = Path.home() / ".devops"
CONFIG_FILE = CONFIG_DIR / "config.json"

# provider -> (default model, API key env names, base URL env names)
PROVIDER_DEFAULTS: dict[str, dict[str, Any]] = {
    "openai": {
        "model": "gpt-4o-mini",
        "base_url": None,
        "api_key_env": ["DEVOPS_API_KEY", "OPENAI_API_KEY", "LLM_API_KEY"],
        "base_url_env": ["DEVOPS_BASE_URL", "OPENAI_BASE_URL", "LLM_BASE_URL"],
        "model_env": ["DEVOPS_MODEL", "OPENAI_MODEL", "LLM_MODEL"],
    },
    "zhipuai": {
        "model": "glm-4-flash",
        "base_url": None,
        "api_key_env": ["DEVOPS_API_KEY", "ZHIPUAI_API_KEY"],
        "base_url_env": ["DEVOPS_BASE_URL"],
        "model_env": ["DEVOPS_MODEL", "ZHIPUAI_MODEL"],
    },
    "deepseek": {
        "model": "deepseek-chat",
        "base_url": "https://api.deepseek.com",
        "api_key_env": ["DEVOPS_API_KEY", "DEEPSEEK_API_KEY"],
        "base_url_env": ["DEVOPS_BASE_URL", "DEEPSEEK_BASE_URL"],
        "model_env": ["DEVOPS_MODEL", "DEEPSEEK_MODEL"],
    },
    "moonshot": {
        "model": "moonshot-v1-8k",
        "base_url": "https://api.moonshot.cn/v1",
        "api_key_env": ["DEVOPS_API_KEY", "MOONSHOT_API_KEY"],
        "base_url_env": ["DEVOPS_BASE_URL", "MOONSHOT_BASE_URL"],
        "model_env": ["DEVOPS_MODEL", "MOONSHOT_MODEL"],
    },
}


@dataclass
class ModelConfig:
    provider: str
    api_key: str
    model: str
    base_url: Optional[str] = None

    def masked(self) -> dict[str, Any]:
        key = self.api_key
        if len(key) > 8:
            masked_key = f"{key[:4]}...{key[-4:]}"
        else:
            masked_key = "****"
        return {
            "provider": self.provider,
            "api_key": masked_key,
            "model": self.model,
            "base_url": self.base_url or "(default)",
        }


def _first_env(names: list[str]) -> Optional[str]:
    for name in names:
        value = os.environ.get(name, "").strip()
        if value:
            return value
    return None


def list_providers() -> list[str]:
    return list(PROVIDER_DEFAULTS.keys())


def config_exists() -> bool:
    return CONFIG_FILE.is_file()


def load_config_file() -> Optional[dict[str, Any]]:
    if not CONFIG_FILE.is_file():
        return None
    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def save_config(config: ModelConfig) -> Path:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    data = asdict(config)
    CONFIG_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    CONFIG_FILE.chmod(0o600)
    return CONFIG_FILE


def load_config(
    *,
    provider: Optional[str] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    base_url: Optional[str] = None,
) -> ModelConfig:
    """Load config: CLI args > config file > environment variables."""
    file_data = load_config_file() or {}

    resolved_provider = (
        provider
        or os.environ.get("DEVOPS_PROVIDER", "").strip()
        or file_data.get("provider", "").strip()
        or "openai"
    ).lower()

    if resolved_provider not in PROVIDER_DEFAULTS:
        supported = ", ".join(list_providers())
        raise ValueError(f"Unsupported provider: {resolved_provider}. Choose: {supported}")

    defaults = PROVIDER_DEFAULTS[resolved_provider]

    resolved_api_key = api_key or file_data.get("api_key", "").strip()
    if not resolved_api_key:
        resolved_api_key = _first_env(defaults["api_key_env"]) or ""
    if not resolved_api_key:
        raise RuntimeError(
            "API Key not configured. Run: devops config\n"
            f"Or set environment variable: {defaults['api_key_env'][0]}"
        )

    resolved_model = (
        model
        or file_data.get("model", "").strip()
        or _first_env(defaults["model_env"])
        or defaults["model"]
    )

    resolved_base_url = base_url
    if resolved_base_url is None:
        file_base = file_data.get("base_url")
        resolved_base_url = (
            file_base.strip() if isinstance(file_base, str) and file_base.strip() else None
        )
    if resolved_base_url is None:
        resolved_base_url = _first_env(defaults["base_url_env"])
    if resolved_base_url is None:
        resolved_base_url = defaults["base_url"]

    return ModelConfig(
        provider=resolved_provider,
        api_key=resolved_api_key,
        model=resolved_model,
        base_url=resolved_base_url,
    )
