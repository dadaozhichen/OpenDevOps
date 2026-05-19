#!/usr/bin/env bash
# Fetch tree-sitter vendor (same logic as pip install build)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
exec python3 "$ROOT/scripts/ensure_vendor_tree_sitter.py"
