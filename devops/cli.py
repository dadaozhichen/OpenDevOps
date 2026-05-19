"""CLI entry: devops <project-path> | devops config"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

from devops import __version__
from devops.config import config_exists
from devops.config_cmd import run_config


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="devops",
        description="Scan source code, extract blocks, analyze with an LLM, and generate README.md",
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
        help="Configure model API (required before first use)",
    )
    config_parser.add_argument(
        "-s",
        "--show",
        action="store_true",
        help="Show current config (API key masked)",
    )

    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Analyze a project and generate README",
    )
    analyze_parser.add_argument(
        "project",
        nargs="?",
        help="Project directory to analyze",
    )
    analyze_parser.add_argument(
        "-o",
        "--output",
        default="README.md",
        help="Output Markdown filename (default: README.md)",
    )
    analyze_parser.add_argument(
        "--provider",
        choices=["openai", "zhipuai", "deepseek", "moonshot"],
        help="Override provider from config file",
    )
    analyze_parser.add_argument(
        "--model",
        dest="model_name",
        help="Override model name from config file",
    )
    analyze_parser.add_argument(
        "--api-key",
        help="Temporary API key (not recommended; may remain in shell history)",
    )
    analyze_parser.add_argument(
        "--base-url",
        help="Temporary API base URL (OpenAI-compatible)",
    )

    # Compatibility: devops /path/to/project (no subcommand)
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
        folder = input("Project directory path: ").strip()
    if not folder:
        print("Error: project path not provided", file=sys.stderr)
        return 1

    if not config_exists() and not args.api_key:
        print(
            "Error: model API not configured. Run first:\n\n"
            "  devops config\n",
            file=sys.stderr,
        )
        return 1

    folder_path = Path(folder).expanduser().resolve()
    if not folder_path.is_dir():
        print(f"Error: not a valid directory: {folder_path}", file=sys.stderr)
        return 1

    try:
        from devops.analysis import analyze_folder, write_project_readme
        from devops.config import load_config

        cfg = load_config(
            provider=args.provider,
            api_key=args.api_key,
            model=args.model_name,
            base_url=args.base_url,
        )
        print(
            f"Analyzing: {folder_path}  "
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
        print(f"Written: {output}")
        return 0
    except KeyboardInterrupt:
        print("\nCancelled", file=sys.stderr)
        return 130
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def main(argv: Optional[list[str]] = None) -> int:
    argv = list(argv) if argv is not None else sys.argv[1:]

    # devops /path/to/project -> treat as analyze
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
        "\nQuick start:\n"
        "  1. devops config          # configure API\n"
        "  2. devops /path/to/project\n",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
