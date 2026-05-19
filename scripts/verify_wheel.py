#!/usr/bin/env python3
"""检查 wheel 是否已包含预编译原生扩展（Release CI 使用）。"""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path

NATIVE_MODULES = (
    "devops/scan/scan_native",
    "devops/tree_sitter/tree_sitter_native",
)


def _normalize(name: str) -> str:
    return name.replace("\\", "/")


def verify_wheel(path: Path) -> list[str]:
    errors: list[str] = []
    with zipfile.ZipFile(path) as zf:
        names = [_normalize(n) for n in zf.namelist()]
        for prefix in NATIVE_MODULES:
            hits = [
                n
                for n in names
                if n.startswith(prefix)
                and (n.endswith(".so") or n.endswith(".pyd"))
            ]
            if not hits:
                errors.append(f"{path.name}: 缺少预编译模块 {prefix} (*.so / *.pyd)")
    return errors


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("用法: python scripts/verify_wheel.py dist/*.whl", file=sys.stderr)
        return 2

    all_errors: list[str] = []
    for arg in argv[1:]:
        path = Path(arg)
        if not path.is_file():
            print(f"跳过（非文件）: {path}", file=sys.stderr)
            continue
        if path.suffix != ".whl":
            print(f"跳过（非 wheel）: {path}", file=sys.stderr)
            continue
        all_errors.extend(verify_wheel(path))

    if all_errors:
        for err in all_errors:
            print(f"错误: {err}", file=sys.stderr)
        return 1

    print(f"已验证 {len(argv) - 1} 个 wheel，均含 scan_native 与 tree_sitter_native。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
