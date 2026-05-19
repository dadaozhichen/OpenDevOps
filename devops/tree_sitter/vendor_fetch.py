"""Fetch tree-sitter core and grammar sources before build (setup.py / CI)."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

VENDOR_ROOT = Path(__file__).resolve().parent / "vendor"

# (dir name, git URL, tag/branch) — must exist on remote (git ls-remote --tags)
REPOS: tuple[tuple[str, str, str], ...] = (
    ("tree-sitter", "https://github.com/tree-sitter/tree-sitter.git", "v0.21.0"),
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
    ("tree-sitter-kotlin", "https://github.com/fwcd/tree-sitter-kotlin.git", "0.3.0"),
    ("tree-sitter-scala", "https://github.com/tree-sitter/tree-sitter-scala.git", "v0.21.0"),
    ("tree-sitter-bash", "https://github.com/tree-sitter/tree-sitter-bash.git", "v0.21.0"),
)

_GIT_QUIET = ["-c", "advice.detachedHead=false"]


def _git_env() -> dict[str, str]:
    env = os.environ.copy()
    env.setdefault("GIT_TERMINAL_PROMPT", "0")
    return env


def _run(cmd: list[str], *, cwd: Path | None = None) -> None:
    if cmd and cmd[0] == "git":
        cmd = ["git", *_GIT_QUIET, *cmd[1:]]
    subprocess.run(
        cmd,
        cwd=cwd,
        check=True,
        env=_git_env(),
    )


def _strip_git_metadata(dest: Path) -> None:
    """Vendor only needs sources; remove .git to avoid detached-HEAD noise in CI logs."""
    git_dir = dest / ".git"
    if git_dir.exists():
        shutil.rmtree(git_dir)


def _repo_marker(name: str, dest: Path) -> Path:
    if name == "tree-sitter":
        return dest / "lib" / "include" / "tree_sitter" / "api.h"
    for sub in ("src/parser.c", "php/src/parser.c", "typescript/src/parser.c"):
        path = dest / sub
        if path.is_file():
            return path
    return dest / "src" / "parser.c"


def _clone_repo(name: str, url: str, ref: str) -> None:
    dest = VENDOR_ROOT / name
    if _repo_marker(name, dest).is_file():
        return

    VENDOR_ROOT.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        shutil.rmtree(dest)

    print(f"==> clone {name} @ {ref}", flush=True)

    try:
        _run(["git", "clone", "--depth", "1", "--branch", ref, url, str(dest)])
        _strip_git_metadata(dest)
        return
    except subprocess.CalledProcessError:
        if dest.exists():
            shutil.rmtree(dest)

    _run(["git", "clone", "--depth", "1", url, str(dest)])
    try:
        _run(["git", "fetch", "--depth", "1", "origin", f"tag {ref}"], cwd=dest)
        _run(["git", "checkout", "-q", "--detach", "FETCH_HEAD"], cwd=dest)
        _strip_git_metadata(dest)
        return
    except subprocess.CalledProcessError:
        if dest.exists():
            shutil.rmtree(dest)

    _run(["git", "clone", "--depth", "1", url, str(dest)])
    _run(["git", "fetch", "--depth", "1", "origin", ref], cwd=dest)
    _run(["git", "checkout", "-q", "--detach", "FETCH_HEAD"], cwd=dest)
    _strip_git_metadata(dest)


def fetch_vendor() -> None:
    """Fetch all vendor trees. Requires git and network access to GitHub."""
    for name, url, ref in REPOS:
        _clone_repo(name, url, ref)


def main() -> int:
    try:
        fetch_vendor()
    except FileNotFoundError:
        print("error: git not found; install git first", file=sys.stderr)
        return 1
    except subprocess.CalledProcessError as exc:
        print(f"error: failed to fetch vendor: {exc}", file=sys.stderr)
        return 1
    print(f"vendor ready: {VENDOR_ROOT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
