"""Analyze code blocks extracted by Tree-sitter via LLM APIs."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal, Optional

from devops.extract import CodeBlock, extract_blocks_from_paths
from devops.models import BaseChatModel, get_chat_model
from devops.ui import thinking

MAX_CODE_LINES = 80
MAX_CHARS_PER_REQUEST = 24_000

OutputLang = Literal["zh", "en"]

_SYSTEM_PROMPT: dict[OutputLang, str] = {
    "zh": """你是一名资深技术文档工程师，擅长从代码和项目结构中提炼清晰、实用的技术文档。

## 输入说明
- 用户提供的是 Tree-sitter 提取的代码块（函数、类、方法等），通常不是完整仓库。
- 单块源码可能被截断（约 80 行以内），省略处会标注。
- 可能缺少完整目录树、部署脚本或配置文件正文；不得编造，无法确认时写「需结合仓库补充」或「根据代码推断（待确认）」。

## 输出要求
1. 使用 Markdown，**简体中文**，专业、客观、条理清晰。
2. 不要大段粘贴源码；最多引用函数/方法签名（例如 `def create_user(name: str) -> int`）。
3. 对公共 API（对外导出的函数、类、CLI 入口）优先用表格：名称 | 参数 | 返回值 | 说明。
4. 区分「事实」（代码中可见）与「推断」（架构意图、部署方式）。
5. 具体章节结构以用户消息中的任务说明为准；单文件分析不写整篇项目 README，项目级总览再写完整章节。

## 禁止
- 虚构不存在的模块、环境变量、命令或依赖。""",
    "en": """You are a senior technical writer who produces clear, practical documentation from code and project structure.

## Input
- The user provides Tree-sitter code blocks (functions, classes, methods, etc.), usually not a full repository.
- Each block may be truncated (about 80 lines); omissions are marked.
- Directory trees, deploy scripts, or full config files may be missing. Do not invent facts; when unsure, write "needs verification in repo" or "inferred (unconfirmed)".

## Output rules
1. Use Markdown in **English**; be professional, objective, and structured.
2. Do not paste large code chunks; at most quote signatures (e.g. `def create_user(name: str) -> int`).
3. For public APIs (exported functions, classes, CLI entrypoints), prefer tables: Name | Parameters | Returns | Description.
4. Separate facts (visible in code) from inferences (architecture intent, deployment).
5. Follow the task structure in the user message; per-file analysis is not a full project README unless asked.

## Forbidden
- Fabricating modules, environment variables, commands, or dependencies that are not supported by the input.""",
}

_FILE_ANALYSIS_PREFIX: dict[OutputLang, str] = {
    "zh": """请分析以下源文件中的代码块，输出 Markdown（不要外层 # 标题，从 ### 小节开始）。

必须包含：
### 职责概述
本文件在项目中的作用（1–3 句）。

### 主要符号
列出重要的类、函数、常量；对公共接口用表格（名称 | 参数 | 返回值 | 说明）。

### 依赖与调用
本文件依赖的项目内模块或第三方库（仅从代码块可见部分归纳）。

### 配置与安全
若出现配置、密钥、路径相关逻辑则简要说明；否则写「本文件未体现」。

### 注意事项
至少 1 条边界情况、潜在风险或改进点；无明显问题时写「未发现明显问题」。

若本文件几乎是项目唯一核心文件，可在末尾增加 ### 项目补充，用 3–5 条要点概括安装/运行/架构（能推断则写，否则标待补充）。

---
""",
    "en": """Analyze the code blocks for the source file below. Output Markdown (no outer # title; start at ### sections).

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
""",
}

_OVERVIEW_PREFIX: dict[OutputLang, str] = {
    "zh": """以下是多个源文件的逐项分析。请生成项目级 Markdown 总览（将写入 README 的「概览」一节）。

必须按顺序包含以下章节（使用 ## 标题）：

## 项目概述
一句话定位 + 核心能力列表（3–6 条）。

## 快速开始
安装、配置、最小运行示例；信息不足时列出「待补充」项。

## 架构设计
模块划分与核心数据流（可用 Mermaid 代码块）。

## 模块与文件关系
各目录/文件如何协作；归纳即可，勿重复粘贴各文件分析全文。

## 配置说明
汇总配置项、环境变量、配置文件路径。

## 依赖关系
关键第三方库与项目内模块依赖（归纳，不罗列依赖文件全文）。

## 部署与运维
构建、启动、日志/输出要点；无法推断则标明「需补充」。

## 常见问题与注意事项
至少 2 条潜在坑点、扫描/分析范围限制或工具约束。

## 架构与质量建议
共性问题或改进建议（3–5 条，可选）。

---
逐项分析如下：

""",
    "en": """Below are per-file analyses. Produce a project-level Markdown overview (for the README "Overview" section).

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

""",
}

_README_LABELS: dict[OutputLang, dict[str, str]] = {
    "zh": {
        "banner": "> 本文档由代码分析工具自动生成。",
        "overview": "## 概览",
        "no_summary": "_暂无分析内容。_",
        "stats": "## 统计",
        "metric": "指标",
        "value": "数值",
        "project_path": "项目路径",
        "files_scanned": "扫描文件数",
        "blocks_extracted": "提取代码块数",
        "files_analyzed": "已分析文件数",
        "generated_at": "生成时间",
        "model": "分析模型",
        "per_file": "## 文件分析",
        "code_blocks": "代码块数量",
        "no_file_analysis": "_无分析结果。_",
        "footer": "*Generated by Devops code analyzer*",
        "empty_blocks": "未提取到任何代码块，请确认目录内有支持的源码文件。",
        "truncated": "...(内容过长已截断)",
    },
    "en": {
        "banner": "> Auto-generated by Devops code analyzer.",
        "overview": "## Overview",
        "no_summary": "_No analysis content._",
        "stats": "## Statistics",
        "metric": "Metric",
        "value": "Value",
        "project_path": "Project path",
        "files_scanned": "Files scanned",
        "blocks_extracted": "Code blocks extracted",
        "files_analyzed": "Files analyzed",
        "generated_at": "Generated at",
        "model": "Model",
        "per_file": "## Per-file analysis",
        "code_blocks": "Code blocks",
        "no_file_analysis": "_No analysis result._",
        "footer": "*Generated by Devops code analyzer*",
        "empty_blocks": "No code blocks extracted. Ensure the directory contains supported source files.",
        "truncated": "...(truncated: content too long)",
    },
}

_PROMPT_META: dict[OutputLang, dict[str, str]] = {
    "zh": {
        "file_path": "文件路径",
        "language": "语言",
        "block_count": "代码块数量",
        "block_label": "块",
        "omit": "省略",
    },
    "en": {
        "file_path": "File path",
        "language": "Language",
        "block_count": "Block count",
        "block_label": "Block",
        "omit": "omitted",
    },
}


def normalize_output_lang(lang: Optional[str]) -> OutputLang:
    if lang is None or not str(lang).strip():
        return "zh"
    v = str(lang).strip().lower()
    if v in ("zh", "cn", "chinese", "中文", "chs", "zh-cn"):
        return "zh"
    if v in ("en", "english", "英文", "en-us"):
        return "en"
    raise ValueError(f"Unsupported output language: {lang!r}. Use zh (default) or en.")


def _truncate_code(code: str, max_lines: int, omit_word: str) -> str:
    lines = code.splitlines()
    if len(lines) <= max_lines:
        return code
    head = "\n".join(lines[:max_lines])
    return f"{head}\n# ... ({len(lines) - max_lines} lines {omit_word})"


def _format_blocks_for_prompt(blocks: list[CodeBlock], lang: OutputLang) -> str:
    labels = _PROMPT_META[lang]
    parts: list[str] = []
    for i, block in enumerate(blocks, 1):
        title = block.name or "(anonymous)"
        parts.append(
            f"### {labels['block_label']} {i}: {block.block_type} `{title}` "
            f"(L{block.start_line}-L{block.end_line})\n"
            f"```{block.language}\n{_truncate_code(block.code, MAX_CODE_LINES, labels['omit'])}\n```"
        )
    return "\n\n".join(parts)


def _chat(model: BaseChatModel, system_prompt: str, prompt: str) -> str:
    with thinking():
        return model.chat(system_prompt, prompt, temperature=0.2)


def analyze_blocks(
    blocks: list[CodeBlock],
    *,
    provider: Optional[str] = None,
    api_key: Optional[str] = None,
    model_name: Optional[str] = None,
    base_url: Optional[str] = None,
    output_lang: Optional[str] = None,
) -> dict[str, Any]:
    """Call the LLM per file and build a project overview."""
    lang = normalize_output_lang(output_lang)
    labels = _README_LABELS[lang]
    meta = _PROMPT_META[lang]
    system_prompt = _SYSTEM_PROMPT[lang]

    chat_model = get_chat_model(
        provider=provider,
        api_key=api_key,
        model=model_name,
        base_url=base_url,
    )

    if not blocks:
        return {
            "summary": labels["empty_blocks"],
            "files": [],
            "blocks_count": 0,
            "output_lang": lang,
        }

    by_file: dict[str, list[CodeBlock]] = defaultdict(list)
    for block in blocks:
        by_file[block.file_path].append(block)

    per_file: list[dict[str, Any]] = []
    file_summaries: list[str] = []

    for file_path, file_blocks in sorted(by_file.items()):
        body = _format_blocks_for_prompt(file_blocks, lang)
        if len(body) > MAX_CHARS_PER_REQUEST:
            body = body[:MAX_CHARS_PER_REQUEST] + f"\n\n{labels['truncated']}"

        prompt = (
            f"{_FILE_ANALYSIS_PREFIX[lang]}"
            f"{meta['file_path']}: {file_path}\n"
            f"{meta['language']}: {file_blocks[0].language}\n"
            f"{meta['block_count']}: {len(file_blocks)}\n\n"
            f"{body}"
        )
        analysis = _chat(chat_model, system_prompt, prompt)
        per_file.append(
            {
                "file_path": file_path,
                "blocks_count": len(file_blocks),
                "analysis": analysis,
            }
        )
        file_summaries.append(f"[{file_path}]\n{analysis}")

    overview_prompt = _OVERVIEW_PREFIX[lang] + "\n\n---\n\n".join(file_summaries)
    if len(overview_prompt) > MAX_CHARS_PER_REQUEST:
        overview_prompt = overview_prompt[:MAX_CHARS_PER_REQUEST] + f"\n{labels['truncated']}"

    summary = (
        _chat(chat_model, system_prompt, overview_prompt)
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
        "output_lang": lang,
    }


def analyze_files(
    paths: list[str],
    *,
    provider: Optional[str] = None,
    api_key: Optional[str] = None,
    model_name: Optional[str] = None,
    base_url: Optional[str] = None,
    output_lang: Optional[str] = None,
) -> dict[str, Any]:
    """Extract blocks from paths and analyze them."""
    blocks = extract_blocks_from_paths(paths)
    return analyze_blocks(
        blocks,
        provider=provider,
        api_key=api_key,
        model_name=model_name,
        base_url=base_url,
        output_lang=output_lang,
    )


def analyze_folder(
    folder: str,
    *,
    provider: Optional[str] = None,
    api_key: Optional[str] = None,
    model_name: Optional[str] = None,
    base_url: Optional[str] = None,
    output_lang: Optional[str] = None,
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
        output_lang=output_lang,
    )
    result["folder"] = str(folder_path)
    result["project_name"] = folder_path.name
    result["scanned_files_count"] = len(paths)
    result["generated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    return result


def render_readme(result: dict[str, Any]) -> str:
    """Render analysis result as README Markdown."""
    lang = normalize_output_lang(result.get("output_lang"))
    labels = _README_LABELS[lang]

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
        labels["banner"],
        "",
        labels["overview"],
        "",
        summary or labels["no_summary"],
        "",
        labels["stats"],
        "",
        f"| {labels['metric']} | {labels['value']} |",
        "| --- | --- |",
        f"| {labels['project_path']} | `{folder}` |",
        f"| {labels['files_scanned']} | {scanned} |",
        f"| {labels['blocks_extracted']} | {blocks} |",
        f"| {labels['files_analyzed']} | {files_count} |",
        f"| {labels['generated_at']} | {generated_at} |",
        f"| {labels['model']} | {result.get('model_provider', '')} / {result.get('model_name', '')} |",
        "",
    ]

    if per_file:
        lines.extend([labels["per_file"], ""])
        for item in per_file:
            rel = item.get("file_path", "")
            if folder and rel.startswith(folder):
                rel = rel[len(folder) :].lstrip("/\\")
            count = item.get("blocks_count", 0)
            analysis = (item.get("analysis") or "").strip()
            lines.append(f"### `{rel}`")
            lines.append("")
            lines.append(f"- **{labels['code_blocks']}**: {count}")
            lines.append("")
            lines.append(analysis or labels["no_file_analysis"])
            lines.append("")

    lines.append("---")
    lines.append("")
    lines.append(labels["footer"])
    lines.append("")
    return "\n".join(lines)


def write_project_readme(folder: str, result: dict[str, Any], filename: str = "README.md") -> Path:
    """Write Markdown to README.md under the target project directory."""
    folder_path = Path(folder).resolve()
    output_path = folder_path / filename
    markdown = render_readme(result)
    output_path.write_text(markdown, encoding="utf-8")
    return output_path
