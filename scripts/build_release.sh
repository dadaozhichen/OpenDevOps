#!/usr/bin/env bash
# Build sdist and platform wheel under dist/ for GitHub Release upload.
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
echo "Artifacts ready (upload to GitHub Release):"
ls -la dist/
