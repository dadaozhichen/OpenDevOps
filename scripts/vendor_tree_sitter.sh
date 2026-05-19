#!/usr/bin/env bash
# 拉取 tree-sitter 核心与各语言 grammar，供 devops/tree_sitter 原生扩展编译使用。
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENDOR="$ROOT/devops/tree_sitter/vendor"
mkdir -p "$VENDOR"

clone_repo() {
  local name="$1"
  local url="$2"
  local ref="$3"
  local dest="$VENDOR/$name"
  if [[ -d "$dest/.git" ]]; then
    echo "==> $name already cloned, fetching $ref"
    git -C "$dest" fetch --depth 1 origin "$ref" 2>/dev/null || git -C "$dest" fetch origin
    git -C "$dest" checkout -q FETCH_HEAD 2>/dev/null || git -C "$dest" checkout -q "$ref"
  else
    echo "==> clone $name @ $ref"
    git clone --depth 1 --branch "$ref" "$url" "$dest" 2>/dev/null \
      || git clone --depth 1 "$url" "$dest" && git -C "$dest" checkout -q "$ref"
  fi
}

# 与 pyproject 中 tree-sitter<0.22 对齐
clone_repo tree-sitter https://github.com/tree-sitter/tree-sitter.git v0.21.3

GRAMMARS=(
  tree-sitter-python|https://github.com/tree-sitter/tree-sitter-python.git|v0.21.0
  tree-sitter-javascript|https://github.com/tree-sitter/tree-sitter-javascript.git|v0.21.0
  tree-sitter-typescript|https://github.com/tree-sitter/tree-sitter-typescript.git|v0.21.0
  tree-sitter-cpp|https://github.com/tree-sitter/tree-sitter-cpp.git|v0.22.0
  tree-sitter-c|https://github.com/tree-sitter/tree-sitter-c.git|v0.21.0
  tree-sitter-java|https://github.com/tree-sitter/tree-sitter-java.git|v0.21.0
  tree-sitter-go|https://github.com/tree-sitter/tree-sitter-go.git|v0.21.0
  tree-sitter-rust|https://github.com/tree-sitter/tree-sitter-rust.git|v0.21.0
  tree-sitter-ruby|https://github.com/tree-sitter/tree-sitter-ruby.git|v0.21.0
  tree-sitter-php|https://github.com/tree-sitter/tree-sitter-php.git|v0.21.0
  tree-sitter-c-sharp|https://github.com/tree-sitter/tree-sitter-c-sharp.git|v0.21.0
  tree-sitter-kotlin|https://github.com/fwcd/tree-sitter-kotlin.git|v0.3.0
  tree-sitter-scala|https://github.com/tree-sitter/tree-sitter-scala.git|v0.21.0
  tree-sitter-bash|https://github.com/tree-sitter/tree-sitter-bash.git|v0.21.0
)

for entry in "${GRAMMARS[@]}"; do
  IFS='|' read -r name url ref <<< "$entry"
  clone_repo "$name" "$url" "$ref"
done

echo "Vendor tree-sitter sources ready under $VENDOR"
