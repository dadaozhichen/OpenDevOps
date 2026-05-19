"""Analyze code blocks extracted by Tree-sitter via LLM APIs."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from devops.extract import CodeBlock, extract_blocks_from_paths
from devops.models import BaseChatModel, get_chat_model
from devops.ui import thinking

MAX_CODE_LINES = 80
MAX_CHARS_PER_REQUEST = 24_000

SYSTEM_PROMPT = """You are a senior technical writer who produces clear, practical documentation from code and project structure.

## Input
- The user provides Tree-sitter code blocks (functions, classes, methods, etc.), usually not a full repository.
- Each block may be truncated (about 80 lines); omissions are marked.
- Directory trees, deploy scripts, or full config files may be missing. Do not invent facts; when unsure, write "needs verification in repo" or "inferred (unconfirmed)".

## Output rules
1. Use Markdown in English; be professional, objective, and structured.
2. Do not paste large code chunks; at most quote signatures (e.g. `def create_user(name: str) -> int`).
3. For public APIs (exported functions, classes, CLI entrypoints), prefer tables: Name | Parameters | Returns | Description.
4. Separate facts (visible in code) from inferences (architecture intent, deployment).
5. Follow the task structure in the user message; per-file analysis is not a full project README unless asked.

## Forbidden
- Fabricating modules, environment variables, commands, or dependencies that are not supported by the input."""

FILE_ANALYSIS_PROMPT_PREFIX = """Analyze the code blocks for the source file below. Output Markdown (no outer # title; start at ### sections).

Required sections:
### Overview
What this file does in the project (1–3 sentences).

### Main symbols
Important classes, functions, and constants; use a table for public APIs (Name | Parameters | Returns | Description).

### Dependencies and calls
In-project modules and third-party libraries visible from the blocks.

### Configuration and security
Brief notes on config, secrets, or paths if present; otherwise write "Not shown in this file".

### Notes
At least one edge case, risk, or improvement; if none, write "No obvious issues found".

If this file is effectively the whole project, add ### Project notes with 3–5 bullets on install/run/architecture (mark gaps as TBD).

---
"""

OVERVIEW_PROMPT_PREFIX = """Below are per-file analyses. Produce a project-level Markdown overview (for the README "Overview" section).

Include these sections in order (use ## headings):

## Project summary
One-line positioning plus 3–6 core capabilities.

## Quick start
Install, configure, and minimal run; list TBD items when information is missing.

## Architecture
Module layout and data flow (Mermaid allowed).

## Modules and files
How directories/files work together; summarize, do not repeat full per-file text.

## Configuration
Config keys, environment variables, and config file paths.

## Dependencies
Key third-party and in-project dependencies (summary only).

## Deployment and operations
Build, start, logging/output; mark unknowns as TBD.

## FAQ and caveats
At least two pitfalls, scan limits, or tool constraints.

## Architecture and quality
3–5 cross-cutting suggestions (optional).

---
Per-file analyses:

"""


def _truncate_code(code: str, max_lines: int = MAX_CODE_LINES) -> str:
    lines = code.splitlines()
    if len(lines) <= max_lines:
        return code
    head = "\n".join(lines[:max_lines])
    return f"{head}\n# ... ({len(lines) - max_lines} lines omitted)"


def _format_blocks_for_prompt(blocks: list[CodeBlock]) -> str:
    parts: list[str] = []
    for i, block in enumerate(blocks, 1):
        title = block.name or "(anonymous)"
        parts.append(
            f"### Block {i}: {block.block_type} `{title}` "
            f"(L{block.start_line}-L{block.end_line})\n"
            f"```{block.language}\n{_truncate_code(block.code)}\n```"
        )
    return "\n\n".join(parts)


def _chat(model: BaseChatModel, prompt: str) -> str:
    with thinking():
        return model.chat(SYSTEM_PROMPT, prompt, temperature=0.2)


def analyze_blocks(
    blocks: list[CodeBlock],
    *,
    provider: Optional[str] = None,
    api_key: Optional[str] = None,
    model_name: Optional[str] = None,
    base_url: Optional[str] = None,
) -> dict[str, Any]:
    """Call the LLM per file and build a project overview."""
    chat_model = get_chat_model(
        provider=provider,
        api_key=api_key,
        model=model_name,
        base_url=base_url,
    )

    if not blocks:
        return {
            "summary": "No code blocks extracted. Ensure the directory contains supported source files.",
            "files": [],
            "blocks_count": 0,
        }

    by_file: dict[str, list[CodeBlock]] = defaultdict(list)
    for block in blocks:
        by_file[block.file_path].append(block)

    per_file: list[dict[str, Any]] = []
    file_summaries: list[str] = []

    for file_path, file_blocks in sorted(by_file.items()):
        body = _format_blocks_for_prompt(file_blocks)
        if len(body) > MAX_CHARS_PER_REQUEST:
            body = body[:MAX_CHARS_PER_REQUEST] + "\n\n...(truncated: content too long)"

        prompt = (
            f"{FILE_ANALYSIS_PROMPT_PREFIX}"
            f"File path: {file_path}\n"
            f"Language: {file_blocks[0].language}\n"
            f"Block count: {len(file_blocks)}\n\n"
            f"{body}"
        )
        analysis = _chat(chat_model, prompt)
        per_file.append(
            {
                "file_path": file_path,
                "blocks_count": len(file_blocks),
                "analysis": analysis,
            }
        )
        file_summaries.append(f"[{file_path}]\n{analysis}")

    overview_prompt = OVERVIEW_PROMPT_PREFIX + "\n\n---\n\n".join(file_summaries)
    if len(overview_prompt) > MAX_CHARS_PER_REQUEST:
        overview_prompt = overview_prompt[:MAX_CHARS_PER_REQUEST] + "\n...(truncated)"

    summary = (
        _chat(chat_model, overview_prompt)
        if len(per_file) > 1
        else per_file[0]["analysis"]
    )

    return {
        "summary": summary,
        "files": per_file,
        "blocks_count": len(blocks),
        "files_count": len(per_file),
        "model_provider": chat_model.config.provider,
        "model_name": chat_model.config.model,
    }


def analyze_files(
    paths: list[str],
    *,
    provider: Optional[str] = None,
    api_key: Optional[str] = None,
    model_name: Optional[str] = None,
    base_url: Optional[str] = None,
) -> dict[str, Any]:
    """Extract blocks from paths and analyze them."""
    blocks = extract_blocks_from_paths(paths)
    return analyze_blocks(
        blocks,
        provider=provider,
        api_key=api_key,
        model_name=model_name,
        base_url=base_url,
    )


def analyze_folder(
    folder: str,
    *,
    provider: Optional[str] = None,
    api_key: Optional[str] = None,
    model_name: Optional[str] = None,
    base_url: Optional[str] = None,
) -> dict[str, Any]:
    """Scan a directory, extract blocks, and analyze."""
    from devops.scan import scan_code_files

    folder_path = Path(folder).resolve()
    paths = scan_code_files(str(folder_path))
    result = analyze_files(
        paths,
        provider=provider,
        api_key=api_key,
        model_name=model_name,
        base_url=base_url,
    )
    result["folder"] = str(folder_path)
    result["project_name"] = folder_path.name
    result["scanned_files_count"] = len(paths)
    result["generated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    return result


def render_readme(result: dict[str, Any]) -> str:
    """Render analysis result as README Markdown."""
    project = result.get("project_name") or Path(result.get("folder", ".")).name
    folder = result.get("folder", "")
    generated_at = result.get("generated_at", "")
    scanned = result.get("scanned_files_count", 0)
    blocks = result.get("blocks_count", 0)
    files_count = result.get("files_count", 0)
    summary = result.get("summary", "").strip()
    per_file: list[dict[str, Any]] = result.get("files", [])

    lines: list[str] = [
        f"# {project}",
        "",
        "> Auto-generated by Devops code analyzer.",
        "",
        "## Overview",
        "",
        summary or "_No analysis content._",
        "",
        "## Statistics",
        "",
        "| Metric | Value |",
        "| --- | --- |",
        f"| Project path | `{folder}` |",
        f"| Files scanned | {scanned} |",
        f"| Code blocks extracted | {blocks} |",
        f"| Files analyzed | {files_count} |",
        f"| Generated at | {generated_at} |",
        f"| Model | {result.get('model_provider', '')} / {result.get('model_name', '')} |",
        "",
    ]

    if per_file:
        lines.extend(["## Per-file analysis", ""])
        for item in per_file:
            rel = item.get("file_path", "")
            if folder and rel.startswith(folder):
                rel = rel[len(folder) :].lstrip("/\\")
            count = item.get("blocks_count", 0)
            analysis = (item.get("analysis") or "").strip()
            lines.append(f"### `{rel}`")
            lines.append("")
            lines.append(f"- **Code blocks**: {count}")
            lines.append("")
            lines.append(analysis or "_No analysis result._")
            lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("*Generated by Devops code analyzer*")
    lines.append("")
    return "\n".join(lines)


def write_project_readme(folder: str, result: dict[str, Any], filename: str = "README.md") -> Path:
    """Write Markdown to README.md under the target project directory."""
    folder_path = Path(folder).resolve()
    output_path = folder_path / filename
    markdown = render_readme(result)
    output_path.write_text(markdown, encoding="utf-8")
    return output_path
