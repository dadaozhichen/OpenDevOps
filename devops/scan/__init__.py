"""Scan project folders for code files (UTF-8 paths, including non-ASCII on Windows)."""

from __future__ import annotations

from pathlib import Path

from devops.scan.scan_native import scan_code_files as _scan_code_files_native


def scan_code_files(folder: str) -> list[str]:
    root = Path(folder).expanduser()
    try:
        root = root.resolve()
    except OSError:
        root = root.absolute()
    return _scan_code_files_native(str(root))


__all__ = ["scan_code_files"]
