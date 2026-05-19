#!/usr/bin/env python3
"""构建前确保 tree-sitter vendor 存在（CI / 本地 pip install 均可调用）。"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from devops.tree_sitter.build_sources import vendor_ready
from devops.tree_sitter.vendor_fetch import fetch_vendor


def main() -> int:
    if vendor_ready():
        print("tree-sitter vendor 已存在，跳过拉取")
        return 0
    fetch_vendor()
    if not vendor_ready():
        print("错误: vendor 拉取后仍不完整", file=sys.stderr)
        return 1
    print("tree-sitter vendor 已就绪")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
