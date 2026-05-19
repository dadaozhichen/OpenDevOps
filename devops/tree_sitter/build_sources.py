
from __future__ import annotations

from pathlib import Path

# 与 setup.py 同级的项目根目录；setuptools 要求源路径为相对路径
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
VENDOR_ROOT = Path(__file__).resolve().parent / "vendor"
TREE_SITTER_CORE = VENDOR_ROOT / "tree-sitter"


def _rel(path: Path) -> str:
    return path.relative_to(PROJECT_ROOT).as_posix()

GRAMMAR_DIRS = (
    "tree-sitter-bash",
    "tree-sitter-c",
    "tree-sitter-c-sharp",
    "tree-sitter-cpp",
    "tree-sitter-go",
    "tree-sitter-java",
    "tree-sitter-javascript",
    "tree-sitter-kotlin",
    "tree-sitter-php",
    "tree-sitter-python",
    "tree-sitter-ruby",
    "tree-sitter-rust",
    "tree-sitter-scala",
    "tree-sitter-typescript",
)

# 部分 grammar 仓库将 src 放在子目录（如新版 php/typescript）
GRAMMAR_SRC_SUBDIRS: dict[str, tuple[str, ...]] = {
    "tree-sitter-php": ("php/src", "src"),
    "tree-sitter-typescript": ("typescript/src", "src"),
}


def _grammar_src_dirs(grammar: str) -> tuple[Path, ...]:
    root = VENDOR_ROOT / grammar
    subdirs = GRAMMAR_SRC_SUBDIRS.get(grammar, ("src",))
    return tuple(root / sub for sub in subdirs)


def vendor_ready() -> bool:
    return (TREE_SITTER_CORE / "lib" / "include" / "tree_sitter" / "api.h").is_file()


def collect_sources() -> tuple[list[str], list[str]]:
    if not vendor_ready():
        raise FileNotFoundError(
            "tree-sitter vendor 未就绪。请先运行: bash scripts/vendor_tree_sitter.sh"
        )

    sources: list[str] = []
    include_dirs: list[str] = [_rel(TREE_SITTER_CORE / "lib" / "include")]

    def add_include(path: Path) -> None:
        s = _rel(path)
        if s not in include_dirs:
            include_dirs.append(s)

    for grammar in GRAMMAR_DIRS:
        parser_c = None
        src_dir = None
        for candidate in _grammar_src_dirs(grammar):
            path = candidate / "parser.c"
            if path.is_file():
                parser_c = path
                src_dir = candidate
                break
        if parser_c is None:
            raise FileNotFoundError(
                f"缺少 grammar 源文件 parser.c,已检查: {_grammar_src_dirs(grammar)}"
            )
        sources.append(_rel(parser_c))
        if (src_dir / "tree_sitter").is_dir():
            add_include(src_dir)
        for scanner_name in ("scanner.c", "scanner.cc"):
            scanner = src_dir / scanner_name
            if scanner.is_file():
                sources.append(_rel(scanner))

    return sources, include_dirs
