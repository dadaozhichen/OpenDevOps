

from __future__ import annotations

from typing import Any, Callable, Optional

_native_get_parser: Optional[Callable[[str], Any]] = None
_parser_cache: dict[str, object] = {}


def _load_native_get_parser() -> Callable[[str], Any]:
    global _native_get_parser
    if _native_get_parser is not None:
        return _native_get_parser
    try:
        from devops.tree_sitter.tree_sitter_native import get_parser

        _native_get_parser = get_parser
        return _native_get_parser
    except ImportError as exc:
        raise ImportError(
            "devops.tree_sitter 原生扩展未安装。请先执行 "
            "bash scripts/vendor_tree_sitter.sh，再运行 pip install -e ."
        ) from exc


def get_parser(language: str):
    if language not in _parser_cache:
        _parser_cache[language] = _load_native_get_parser()(language)
    return _parser_cache[language]


__all__ = ["get_parser"]
