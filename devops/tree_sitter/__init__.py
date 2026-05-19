

from __future__ import annotations

try:
    from devops.tree_sitter.tree_sitter_native import get_parser as _native_get_parser
except ImportError as exc:
    raise ImportError(
        "devops.tree_sitter 原生扩展未安装。请先执行 "
        "bash scripts/vendor_tree_sitter.sh,再运行 pip install -e ."
    ) from exc

_parser_cache: dict[str, object] = {}


def get_parser(language: str):
    if language not in _parser_cache:
        _parser_cache[language] = _native_get_parser(language)
    return _parser_cache[language]


__all__ = ["get_parser"]
