"""Loglama yapılandırması."""

from __future__ import annotations

import logging
from typing import Optional

from rich.logging import RichHandler

_initialized = False


def setup_logging(verbose: bool = False, quiet: bool = False) -> None:
    """Rich tabanlı loglama sistemini başlatır."""
    global _initialized

    level = logging.WARNING if quiet else (logging.DEBUG if verbose else logging.INFO)

    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[
            RichHandler(
                rich_tracebacks=True,
                markup=True,
                show_path=verbose,
            )
        ],
    )
    _initialized = True


def get_logger(name: str) -> logging.Logger:
    """Modül adına göre logger döndürür."""
    if not _initialized:
        setup_logging()
    return logging.getLogger(name)
