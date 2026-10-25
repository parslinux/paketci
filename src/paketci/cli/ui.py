"""Rich tabanlı UI yardımcıları — progress, tablo, log."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Generator, Optional

from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
    TransferSpeedColumn,
)
from rich.table import Table
from rich.theme import Theme

# ─── Konsol ──────────────────────────────────────────────────────────────────

THEME = Theme(
    {
        "info": "bold cyan",
        "success": "bold green",
        "warning": "bold yellow",
        "error": "bold red",
        "package": "magenta",
        "version": "dim",
        "dim": "dim white",
    }
)

console = Console(theme=THEME)
err_console = Console(stderr=True, theme=THEME)


# ─── Mesaj Yardımcıları ───────────────────────────────────────────────────────

def info(msg: str) -> None:
    console.print(f"[info]ℹ[/]  {msg}")


def success(msg: str) -> None:
    console.print(f"[success]✔[/]  {msg}")


def warn(msg: str) -> None:
    err_console.print(f"[warning]⚠[/]  {msg}")


def error(msg: str) -> None:
    err_console.print(f"[error]✖[/]  {msg}")


def print_error_panel(title: str, body: str) -> None:
    err_console.print(
        Panel(body, title=f"[error]{title}[/]", border_style="red", expand=False)
    )


# ─── Spinner ─────────────────────────────────────────────────────────────────

@contextmanager
def spinner(text: str) -> Generator[None, None, None]:
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        console=console,
        transient=True,
    ) as prog:
        prog.add_task(text, total=None)
        yield


# ─── Tablo ───────────────────────────────────────────────────────────────────

def make_package_table(
    packages: list[tuple[str, str, str]],  # (name, version, note)
    title: str = "Paketler",
) -> Table:
    tbl = Table(title=title, show_lines=False, header_style="bold cyan")
    tbl.add_column("Paket", style="package", min_width=25)
    tbl.add_column("Versiyon", style="version", justify="right")
    tbl.add_column("Notlar", style="dim")

    for name, version, note in packages:
        tbl.add_row(name, version, note)

    return tbl
