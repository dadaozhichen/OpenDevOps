#!/usr/bin/env bash
# 生成本地 dist/ 下的 sdist 与当前平台 wheel，可直接作为 GitHub Release 附件上传。
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if ! python3 -c "import build" 2>/dev/null; then
  python3 -m pip install -U pip
  python3 -m pip install "build>=1.2.0"
fi

rm -rf dist build *.egg-info
python3 -m build --outdir dist "$@"

echo ""
echo "制品已生成（可上传到 GitHub Release）："
ls -la dist/
