#!/usr/bin/env bash
# 拉取 tree-sitter vendor（与 pip install 构建时自动执行的逻辑相同）
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
exec python3 "$ROOT/scripts/ensure_vendor_tree_sitter.py"
