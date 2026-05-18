"""终端入口：devops <项目路径> | devops config"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from devops import __version__
from devops.analysis import analyze_folder, write_project_readme
from devops.config import config_exists
from devops.config_cmd import run_config


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="devops",
        description="扫描项目源码，提取代码块，调用大模型分析并生成 README.md",
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command")

    config_parser = subparsers.add_parser(
        "config",
        help="配置模型 API（首次使用前必须执行）",
    )
    config_parser.add_argument(
        "-s",
        "--show",
        action="store_true",
        help="查看当前配置（API Key 脱敏）",
    )

    analyze_parser = subparsers.add_parser(
        "analyze",
        help="分析项目并生成 README",
    )
    analyze_parser.add_argument(
        "project",
        nargs="?",
        help="要分析的项目目录路径",
    )
    analyze_parser.add_argument(
        "-o",
        "--output",
        default="README.md",
        help="输出 Markdown 文件名（默认: README.md）",
    )
    analyze_parser.add_argument(
        "--provider",
        choices=["openai", "zhipuai", "deepseek", "moonshot"],
        help="覆盖配置文件中的模型提供商",
    )
    analyze_parser.add_argument(
        "--model",
        dest="model_name",
        help="覆盖配置文件中的模型名称",
    )
    analyze_parser.add_argument(
        "--api-key",
        help="临时指定 API Key（不推荐，会留在 shell 历史）",
    )
    analyze_parser.add_argument(
        "--base-url",
        help="临时指定 API Base URL（OpenAI 兼容接口）",
    )

    # 兼容: devops /path/to/project（无子命令）
    parser.add_argument(
        "project_legacy",
        nargs="?",
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "-o",
        "--output",
        default="README.md",
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--provider",
        choices=["openai", "zhipuai", "deepseek", "moonshot"],
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--model",
        dest="model_name",
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--api-key",
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--base-url",
        help=argparse.SUPPRESS,
    )

    return parser


def _run_analyze(args: argparse.Namespace) -> int:
    folder = getattr(args, "project", None) or getattr(args, "project_legacy", None)
    if not folder:
        folder = input("请输入项目文件夹路径: ").strip()
    if not folder:
        print("错误: 未提供项目路径", file=sys.stderr)
        return 1

    if not config_exists() and not args.api_key:
        print(
            "错误: 尚未配置模型 API。请先运行:\n\n"
            "  devops config\n",
            file=sys.stderr,
        )
        return 1

    folder_path = Path(folder).expanduser().resolve()
    if not folder_path.is_dir():
        print(f"错误: 不是有效目录: {folder_path}", file=sys.stderr)
        return 1

    try:
        from devops.config import load_config

        cfg = load_config(
            provider=args.provider,
            api_key=args.api_key,
            model=args.model_name,
            base_url=args.base_url,
        )
        print(
            f"正在分析: {folder_path}  "
            f"[{cfg.provider} / {cfg.model}]"
        )
        result = analyze_folder(
            str(folder_path),
            provider=args.provider,
            api_key=args.api_key,
            model_name=args.model_name,
            base_url=args.base_url,
        )
        output = write_project_readme(
            str(folder_path), result, filename=args.output
        )
        print(f"已生成: {output}")
        return 0
    except KeyboardInterrupt:
        print("\n已取消", file=sys.stderr)
        return 130
    except Exception as exc:
        print(f"错误: {exc}", file=sys.stderr)
        return 1


def main(argv: list[str] | None = None) -> int:
    argv = list(argv) if argv is not None else sys.argv[1:]

    # devops /path/to/project -> 自动当作 analyze
    if argv and not argv[0].startswith("-") and argv[0] not in ("config", "analyze"):
        argv = ["analyze", *argv]

    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "config":
        extra = ["--show"] if args.show else []
        return run_config(extra)

    if args.command == "analyze" or args.project_legacy is not None:
        return _run_analyze(args)

    parser.print_help()
    print(
        "\n快速开始:\n"
        "  1. devops config          # 首次配置 API\n"
        "  2. devops /path/to/project\n",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
