"""Terminal UI helpers (spinner, etc.)."""

from __future__ import annotations

import sys
import threading
from contextlib import contextmanager
from typing import Iterator

_SPINNER = ("⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏")


@contextmanager
def thinking(message: str = "thinking") -> Iterator[None]:
    """Show a spinner and label on stderr while a blocking operation runs."""
    if not sys.stderr.isatty():
        print(f"{message}...", file=sys.stderr, flush=True)
        yield
        return

    stop = threading.Event()
    prefix = f"{message} "

    def _spin() -> None:
        i = 0
        while not stop.wait(0.08):
            frame = _SPINNER[i % len(_SPINNER)]
            sys.stderr.write(f"\r{frame} {prefix}")
            sys.stderr.flush()
            i += 1

    thread = threading.Thread(target=_spin, daemon=True)
    thread.start()
    try:
        yield
    finally:
        stop.set()
        thread.join(timeout=0.5)
        clear = "\r" + " " * (len(prefix) + 2) + "\r"
        sys.stderr.write(clear)
        sys.stderr.flush()
