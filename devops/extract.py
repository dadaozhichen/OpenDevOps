"""用 Tree-sitter 从源码文件中提取代码块。"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Iterator, Optional, Union

from devops.scan import scan_code_files

if TYPE_CHECKING:
    from tree_sitter import Node, Tree

EXT_TO_LANGUAGE: dict[str, str] = {
    ".py": "python",
    ".pyw": "python",
    ".js": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".h": "cpp",
    ".hh": "cpp",
    ".hpp": "cpp",
    ".hxx": "cpp",
    ".c": "c",
    ".java": "java",
    ".go": "go",
    ".rs": "rust",
    ".rb": "ruby",
    ".php": "php",
    ".cs": "c_sharp",
    ".kt": "kotlin",
    ".scala": "scala",
    ".sh": "bash",
}

LANGUAGE_NODE_TYPES: dict[str, tuple[str, ...]] = {
    "python": ("function_definition", "async_function_definition", "class_definition"),
    "javascript": (
        "function_declaration",
        "class_declaration",
        "method_definition",
    ),
    "typescript": (
        "function_declaration",
        "class_declaration",
        "method_definition",
        "interface_declaration",
    ),
    "cpp": ("function_definition", "class_specifier", "struct_specifier", "namespace_definition"),
    "c": ("function_definition", "struct_specifier"),
    "java": ("method_declaration", "class_declaration", "interface_declaration"),
    "go": ("function_declaration", "method_declaration", "type_declaration"),
    "rust": ("function_item", "impl_item", "struct_item", "enum_item", "trait_item"),
    "ruby": ("method", "class", "module"),
    "php": ("function_definition", "method_declaration", "class_declaration"),
    "c_sharp": ("method_declaration", "class_declaration", "interface_declaration"),
    "kotlin": ("function_declaration", "class_declaration"),
    "scala": ("function_definition", "class_definition", "object_definition"),
    "bash": ("function_definition",),
}

@dataclass
class CodeBlock:
    file_path: str
    language: str
    block_type: str
    name: str
    start_line: int
    end_line: int
    code: str

    def to_dict(self) -> dict:
        return asdict(self)


def language_for_path(path: Union[str, Path]) -> Optional[str]:
    return EXT_TO_LANGUAGE.get(Path(path).suffix.lower())


def _read_source(path: Path) -> Optional[bytes]:
    try:
        return path.read_bytes()
    except OSError:
        return None


def _line_number(source: bytes, byte_offset: int) -> int:
    return source[:byte_offset].count(b"\n") + 1


def _declarator_name(node: Node) -> str:
    inner = node.child_by_field_name("declarator")
    if inner is not None:
        return _declarator_name(inner)
    if node.type in ("identifier", "field_identifier", "operator_name"):
        return node.text.decode("utf-8", errors="replace")
    for child in node.children:
        name = _declarator_name(child)
        if name:
            return name
    return ""


def _node_name(node: Node, language: str) -> str:
    name_node = node.child_by_field_name("name")
    if name_node is not None:
        return name_node.text.decode("utf-8", errors="replace")

    if language == "python" and node.type == "decorated_definition":
        for child in node.children:
            if child.type in ("function_definition", "class_definition"):
                return _node_name(child, language)

    if language == "cpp" and node.type == "function_definition":
        decl = node.child_by_field_name("declarator")
        if decl is not None:
            return _declarator_name(decl)

    for child in node.children:
        if child.type in ("identifier", "type_identifier", "property_identifier"):
            text = child.text.decode("utf-8", errors="replace")
            if text not in ("def", "class", "fn", "function"):
                return text
    return ""


def _walk_nodes(node: Node) -> Iterator[Node]:
    yield node
    for child in node.children:
        yield from _walk_nodes(child)


def _extract_from_tree(
    tree: Tree,
    source: bytes,
    file_path: str,
    language: str,
) -> list[CodeBlock]:
    target_types = set(LANGUAGE_NODE_TYPES.get(language, ()))
    if not target_types:
        return []

    blocks: list[CodeBlock] = []
    seen: set[tuple[int, int]] = set()

    for node in _walk_nodes(tree.root_node):
        if node.type not in target_types:
            continue
        key = (node.start_byte, node.end_byte)
        if key in seen:
            continue
        seen.add(key)

        blocks.append(
            CodeBlock(
                file_path=file_path,
                language=language,
                block_type=node.type,
                name=_node_name(node, language),
                start_line=_line_number(source, node.start_byte),
                end_line=_line_number(source, node.end_byte),
                code=source[node.start_byte : node.end_byte].decode(
                    "utf-8", errors="replace"
                ),
            )
        )

    blocks.sort(key=lambda b: (b.start_line, b.name))
    return blocks


def extract_blocks_from_file(path: Union[str, Path]) -> list[CodeBlock]:
    p = Path(path)
    language = language_for_path(p)
    if language is None:
        return []

    source = _read_source(p)
    if source is None:
        return []

    try:
        from devops.tree_sitter import get_parser

        tree = get_parser(language).parse(source)
    except Exception:
        return []

    return _extract_from_tree(tree, source, str(p.resolve()), language)


def extract_blocks_from_paths(paths: list[str]) -> list[CodeBlock]:
    blocks: list[CodeBlock] = []
    for path in paths:
        blocks.extend(extract_blocks_from_file(path))
    return blocks


def extract_blocks_from_folder(folder: str) -> list[CodeBlock]:
    return extract_blocks_from_paths(scan_code_files(folder))
