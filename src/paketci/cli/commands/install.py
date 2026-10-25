"""install komutu — paketci install"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Optional

import typer

from paketci.cli import ui
from paketci.core import exceptions, operations

app = typer.Typer()


@app.command("install")
def install_cmd(
    frozen: Annotated[bool, typer.Option("--frozen-lockfile", help="Lockfile'ı değiştirmeden kur (CI için)")] = False,
    offline: Annotated[bool, typer.Option("--offline")] = False,
    target: Annotated[Optional[Path], typer.Option("--target", "-t", help="Hedef site-packages dizini")] = None,
) -> None:
    """Lockfile'daki tüm paketleri kurar. Resolver çalışmaz."""
    try:
        with ui.spinner("Paketler kuruluyor..."):
            operations.install(frozen=frozen, offline=offline, target=target)
        ui.success("Tüm paketler kuruldu.")
    except exceptions.LockfileError as exc:
        ui.print_error_panel("Lockfile Hatası", str(exc))
        raise typer.Exit(code=1)
    except exceptions.PaketciError as exc:
        ui.print_error_panel("Hata", str(exc))
        raise typer.Exit(code=1)
