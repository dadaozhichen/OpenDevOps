"""devops config 子命令：交互式配置模型 API。"""

from __future__ import annotations

import getpass
import sys

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
        print(f"\n配置文件路径: {CONFIG_FILE}", file=sys.stderr)
        return 1

    print("当前模型配置:")
    for key, value in config.masked().items():
        print(f"  {key}: {value}")
    print(f"\n配置文件: {CONFIG_FILE}")
    return 0


def run_config_interactive() -> int:
    providers = list_providers()
    print("支持的模型提供商:")
    for i, name in enumerate(providers, 1):
        print(f"  {i}. {name}")
    print()

    provider = _prompt("提供商 (openai/zhipuai/deepseek/moonshot)", "openai").lower()
    if provider not in providers:
        print(f"错误: 未知提供商 {provider}", file=sys.stderr)
        return 1

    api_key = getpass.getpass("API Key (输入不可见): ").strip()
    if not api_key:
        print("错误: API Key 不能为空", file=sys.stderr)
        return 1

    default_models = {
        "openai": "gpt-4o-mini",
        "zhipuai": "glm-4-flash",
        "deepseek": "deepseek-chat",
        "moonshot": "moonshot-v1-8k",
    }
    model = _prompt("模型名称", default_models.get(provider, "gpt-4o-mini"))

    base_url = ""
    if provider in ("openai",):
        base_url = _prompt("Base URL (留空=官方 OpenAI)", "")
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
    print(f"\n配置已保存: {path}")
    print("现在可以运行: devops /path/to/your/project")
    return 0


def run_config(argv: list[str] | None = None) -> int:
    args = argv or []
    if "--show" in args or "-s" in args:
        return run_config_show()
    return run_config_interactive()
