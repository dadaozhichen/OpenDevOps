#!/usr/bin/env python3
"""Ensure tree-sitter vendor exists before build (CI / local pip install)."""

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
        print("tree-sitter vendor already present, skip fetch")
        return 0
    fetch_vendor()
    if not vendor_ready():
        print("error: vendor incomplete after fetch", file=sys.stderr)
        return 1
    print("tree-sitter vendor ready")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
