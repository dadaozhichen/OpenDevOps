"""调用大模型 API 分析 extract 提取的代码块。"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from devops.extract import CodeBlock, extract_blocks_from_paths
from devops.models import BaseChatModel, get_chat_model

MAX_CODE_LINES = 80
MAX_CHARS_PER_REQUEST = 24_000

SYSTEM_PROMPT = """你是一名资深代码审查专家。
请根据给出的代码块，输出简洁、结构化的中文分析，包含：
1. 文件/模块职责概述
2. 主要函数/类的作用
3. 潜在问题或改进建议（如有）
4. 关键依赖或调用关系（如能看出）

直接输出分析正文，不要重复粘贴完整源码。"""


def _truncate_code(code: str, max_lines: int = MAX_CODE_LINES) -> str:
    lines = code.splitlines()
    if len(lines) <= max_lines:
        return code
    head = "\n".join(lines[:max_lines])
    return f"{head}\n# ... (省略 {len(lines) - max_lines} 行)"


def _format_blocks_for_prompt(blocks: list[CodeBlock]) -> str:
    parts: list[str] = []
    for i, block in enumerate(blocks, 1):
        title = block.name or "(anonymous)"
        parts.append(
            f"### 块 {i}: {block.block_type} `{title}` "
            f"(L{block.start_line}-L{block.end_line})\n"
            f"```{block.language}\n{_truncate_code(block.code)}\n```"
        )
    return "\n\n".join(parts)


def _chat(model: BaseChatModel, prompt: str) -> str:
    return model.chat(SYSTEM_PROMPT, prompt, temperature=0.2)


def analyze_blocks(
    blocks: list[CodeBlock],
    *,
    provider: str | None = None,
    api_key: str | None = None,
    model_name: str | None = None,
    base_url: str | None = None,
) -> dict[str, Any]:
    """按文件分批调用大模型，并生成总览。"""
    chat_model = get_chat_model(
        provider=provider,
        api_key=api_key,
        model=model_name,
        base_url=base_url,
    )

    if not blocks:
        return {
            "summary": "未提取到任何代码块，请确认目录内有支持的源码文件。",
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
            body = body[:MAX_CHARS_PER_REQUEST] + "\n\n...(内容过长已截断)"

        prompt = (
            f"文件路径: {file_path}\n"
            f"语言: {file_blocks[0].language}\n"
            f"代码块数量: {len(file_blocks)}\n\n"
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
        file_summaries.append(f"【{file_path}】\n{analysis}")

    overview_prompt = (
        "以下是多个源文件的逐项分析，请生成一份项目级总览（中文）：\n"
        "1. 项目整体结构\n"
        "2. 各文件之间的关系\n"
        "3. 共性问题或架构建议\n\n"
        + "\n\n---\n\n".join(file_summaries)
    )
    if len(overview_prompt) > MAX_CHARS_PER_REQUEST:
        overview_prompt = overview_prompt[:MAX_CHARS_PER_REQUEST] + "\n...(已截断)"

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
    provider: str | None = None,
    api_key: str | None = None,
    model_name: str | None = None,
    base_url: str | None = None,
) -> dict[str, Any]:
    """从文件路径列表提取代码块并分析。"""
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
    provider: str | None = None,
    api_key: str | None = None,
    model_name: str | None = None,
    base_url: str | None = None,
) -> dict[str, Any]:
    """扫描目录、提取代码块并分析。"""
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
    """将分析结果渲染为 README Markdown 正文。"""
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
        "> 本文档由代码分析工具自动生成。",
        "",
        "## 概览",
        "",
        summary or "_暂无分析内容。_",
        "",
        "## 统计",
        "",
        "| 指标 | 数值 |",
        "| --- | --- |",
        f"| 项目路径 | `{folder}` |",
        f"| 扫描文件数 | {scanned} |",
        f"| 提取代码块数 | {blocks} |",
        f"| 已分析文件数 | {files_count} |",
        f"| 生成时间 | {generated_at} |",
        f"| 分析模型 | {result.get('model_provider', '')} / {result.get('model_name', '')} |",
        "",
    ]

    if per_file:
        lines.extend(["## 文件分析", ""])
        for item in per_file:
            rel = item.get("file_path", "")
            if folder and rel.startswith(folder):
                rel = rel[len(folder) :].lstrip("/\\")
            count = item.get("blocks_count", 0)
            analysis = (item.get("analysis") or "").strip()
            lines.append(f"### `{rel}`")
            lines.append("")
            lines.append(f"- **代码块数量**: {count}")
            lines.append("")
            lines.append(analysis or "_无分析结果。_")
            lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("*Generated by Devops code analyzer*")
    lines.append("")
    return "\n".join(lines)


def write_project_readme(folder: str, result: dict[str, Any], filename: str = "README.md") -> Path:
    """将 Markdown 写入目标项目目录下的 README.md。"""
    folder_path = Path(folder).resolve()
    output_path = folder_path / filename
    markdown = render_readme(result)
    output_path.write_text(markdown, encoding="utf-8")
    return output_path
