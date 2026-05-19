"""devops config subcommand: interactive model API setup."""

from __future__ import annotations

import getpass
import sys
from typing import Optional

from devops.config import (
    CONFIG_FILE,
    ModelConfig,
    list_providers,
    load_config,
    save_config,
)


def _prompt(label: str, default: str = "") -> str:
    if default:
        value = input(f"{label} [{default}]: ").strip()
        return value or default
    return input(f"{label}: ").strip()


def run_config_show() -> int:
    try:
        config = load_config()
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        print(f"\nConfig file: {CONFIG_FILE}", file=sys.stderr)
        return 1

    print("Current model config:")
    for key, value in config.masked().items():
        print(f"  {key}: {value}")
    print(f"\nConfig file: {CONFIG_FILE}")
    return 0


def run_config_interactive() -> int:
    providers = list_providers()
    print("Supported providers:")
    for i, name in enumerate(providers, 1):
        print(f"  {i}. {name}")
    print()

    provider = _prompt("Provider (openai/zhipuai/deepseek/moonshot)", "openai").lower()
    if provider not in providers:
        print(f"Error: unknown provider {provider}", file=sys.stderr)
        return 1

    api_key = getpass.getpass("API Key (hidden): ").strip()
    if not api_key:
        print("Error: API Key cannot be empty", file=sys.stderr)
        return 1

    default_models = {
        "openai": "gpt-4o-mini",
        "zhipuai": "glm-4-flash",
        "deepseek": "deepseek-chat",
        "moonshot": "moonshot-v1-8k",
    }
    model = _prompt("Model name", default_models.get(provider, "gpt-4o-mini"))

    base_url = ""
    if provider in ("openai",):
        base_url = _prompt("Base URL (empty = official OpenAI)", "")
    elif provider in ("deepseek", "moonshot"):
        from devops.config import PROVIDER_DEFAULTS

        default_url = PROVIDER_DEFAULTS[provider]["base_url"] or ""
        base_url = _prompt("Base URL", default_url)

    config = ModelConfig(
        provider=provider,
        api_key=api_key,
        model=model,
        base_url=base_url or None,
    )
    path = save_config(config)
    print(f"\nConfig saved: {path}")
    print("You can now run: devops /path/to/your/project")
    return 0


def run_config(argv: Optional[list[str]] = None) -> int:
    args = argv or []
    if "--show" in args or "-s" in args:
        return run_config_show()
    return run_config_interactive()
