"""构建前拉取 tree-sitter 核心与各语言 grammar（供 setup.py / CI 调用）。"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

VENDOR_ROOT = Path(__file__).resolve().parent / "vendor"

# (目录名, git URL, tag/branch)
REPOS: tuple[tuple[str, str, str], ...] = (
    ("tree-sitter", "https://github.com/tree-sitter/tree-sitter.git", "v0.21.3"),
    ("tree-sitter-python", "https://github.com/tree-sitter/tree-sitter-python.git", "v0.21.0"),
    ("tree-sitter-javascript", "https://github.com/tree-sitter/tree-sitter-javascript.git", "v0.21.0"),
    ("tree-sitter-typescript", "https://github.com/tree-sitter/tree-sitter-typescript.git", "v0.21.0"),
    ("tree-sitter-cpp", "https://github.com/tree-sitter/tree-sitter-cpp.git", "v0.22.0"),
    ("tree-sitter-c", "https://github.com/tree-sitter/tree-sitter-c.git", "v0.21.0"),
    ("tree-sitter-java", "https://github.com/tree-sitter/tree-sitter-java.git", "v0.21.0"),
    ("tree-sitter-go", "https://github.com/tree-sitter/tree-sitter-go.git", "v0.21.0"),
    ("tree-sitter-rust", "https://github.com/tree-sitter/tree-sitter-rust.git", "v0.21.0"),
    ("tree-sitter-ruby", "https://github.com/tree-sitter/tree-sitter-ruby.git", "v0.21.0"),
    ("tree-sitter-php", "https://github.com/tree-sitter/tree-sitter-php.git", "v0.21.0"),
    ("tree-sitter-c-sharp", "https://github.com/tree-sitter/tree-sitter-c-sharp.git", "v0.21.0"),
    ("tree-sitter-kotlin", "https://github.com/fwcd/tree-sitter-kotlin.git", "v0.3.0"),
    ("tree-sitter-scala", "https://github.com/tree-sitter/tree-sitter-scala.git", "v0.21.0"),
    ("tree-sitter-bash", "https://github.com/tree-sitter/tree-sitter-bash.git", "v0.21.0"),
)


def _run(cmd: list[str], *, cwd: Path | None = None) -> None:
    subprocess.run(cmd, cwd=cwd, check=True)


def _clone_repo(name: str, url: str, ref: str) -> None:
    dest = VENDOR_ROOT / name
    if name == "tree-sitter":
        marker = dest / "lib" / "include" / "tree_sitter" / "api.h"
    else:
        marker = dest / "src" / "parser.c"
        if not marker.is_file():
            marker = dest / "php" / "src" / "parser.c"
        if not marker.is_file():
            marker = dest / "typescript" / "src" / "parser.c"
    if marker.is_file():
        return

    VENDOR_ROOT.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        import shutil

        shutil.rmtree(dest)

    print(f"==> clone {name} @ {ref}", flush=True)
    try:
        _run(
            ["git", "clone", "--depth", "1", "--branch", ref, url, str(dest)],
        )
    except subprocess.CalledProcessError:
        _run(["git", "clone", "--depth", "1", url, str(dest)])
        _run(["git", "checkout", "-q", ref], cwd=dest)


def fetch_vendor() -> None:
    """拉取全部 vendor；需要本机已安装 git 且能访问 GitHub。"""
    for name, url, ref in REPOS:
        _clone_repo(name, url, ref)


def main() -> int:
    try:
        fetch_vendor()
    except FileNotFoundError:
        print("错误: 未找到 git，请先安装 git", file=sys.stderr)
        return 1
    except subprocess.CalledProcessError as exc:
        print(f"错误: 拉取 vendor 失败: {exc}", file=sys.stderr)
        return 1
    print(f"Vendor 已就绪: {VENDOR_ROOT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
