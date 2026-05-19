#!/usr/bin/env python3
"""Check that wheels contain prebuilt native extensions (Release CI)."""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path

NATIVE_MODULES = (
    "devops/scan/scan_native",
    "devops/tree_sitter/tree_sitter_native",
)


def _configure_stdio() -> None:
    """Avoid UnicodeEncodeError on Windows runners (cp1252 console)."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except (OSError, ValueError):
                pass


def _normalize(name: str) -> str:
    return name.replace("\\", "/")


def verify_wheel(path: Path) -> list[str]:
    errors: list[str] = []
    with zipfile.ZipFile(path) as zf:
        names = [_normalize(n) for n in zf.namelist()]
        for prefix in NATIVE_MODULES:
            hits = [
                n
                for n in names
                if n.startswith(prefix)
                and (n.endswith(".so") or n.endswith(".pyd"))
            ]
            if not hits:
                errors.append(
                    f"{path.name}: missing prebuilt module {prefix} (*.so / *.pyd)"
                )
    return errors


def main(argv: list[str]) -> int:
    _configure_stdio()

    if len(argv) < 2:
        print("usage: python scripts/verify_wheel.py dist/*.whl", file=sys.stderr)
        return 2

    checked = 0
    all_errors: list[str] = []
    for arg in argv[1:]:
        path = Path(arg)
        if not path.is_file():
            print(f"skip (not a file): {path}", file=sys.stderr)
            continue
        if path.suffix != ".whl":
            print(f"skip (not a wheel): {path}", file=sys.stderr)
            continue
        checked += 1
        all_errors.extend(verify_wheel(path))

    if all_errors:
        for err in all_errors:
            print(f"error: {err}", file=sys.stderr)
        return 1

    print(
        f"verified {checked} wheel(s): scan_native and tree_sitter_native present."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
