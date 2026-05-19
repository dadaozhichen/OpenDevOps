"""调用大模型 API 分析 extract 提取的代码块。"""

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

SYSTEM_PROMPT = """你是一名资深技术文档工程师，擅长从代码和项目结构中提炼出清晰、实用的技术文档。

## 输入说明
- 用户提供的是 Tree-sitter 提取的代码块（函数、类、方法等），通常不是完整仓库。
- 单块源码可能被截断（约 80 行以内），省略处会标注。
- 可能缺少完整目录树、部署脚本或配置文件正文；不得编造，无法确认时写「需结合仓库补充」或「根据代码推断（待确认）」。

## 通用输出要求
1. 使用 Markdown，简体中文，专业、客观、条理清晰。
2. 不要大段粘贴源码；最多引用函数/方法签名（例如 `def create_user(name: str) -> int`）。
3. 对公共 API（对外导出的函数、类、CLI 入口）优先用表格：名称 | 参数 | 返回值 | 说明。
4. 区分「事实」（代码中可见）与「推断」（架构意图、部署方式）。
5. 具体章节结构以用户消息中的任务说明为准；单文件分析不写整篇项目 README，项目级总览再写完整章节。

## 禁止
- 虚构不存在的模块、环境变量、命令或依赖。"""

FILE_ANALYSIS_PROMPT_PREFIX = """请分析以下源文件中的代码块，输出 Markdown（不要外层 # 标题，从 ### 小节开始）。

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
"""

OVERVIEW_PROMPT_PREFIX = """以下是多个源文件的逐项分析。请生成项目级 Markdown 总览（将写入 README 的「概览」一节）。

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

"""


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
            f"{FILE_ANALYSIS_PROMPT_PREFIX}"
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

    overview_prompt = OVERVIEW_PROMPT_PREFIX + "\n\n---\n\n".join(file_summaries)
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
    provider: Optional[str] = None,
    api_key: Optional[str] = None,
    model_name: Optional[str] = None,
    base_url: Optional[str] = None,
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
    provider: Optional[str] = None,
    api_key: Optional[str] = None,
    model_name: Optional[str] = None,
    base_url: Optional[str] = None,
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
