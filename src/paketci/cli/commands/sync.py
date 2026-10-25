"""sync komutu — paketci sync"""

from __future__ import annotations

from typing import Annotated

import typer

from paketci.cli import ui
from paketci.core import exceptions, operations

app = typer.Typer()


@app.command("sync")
def sync_cmd(
    frozen: Annotated[bool, typer.Option("--frozen-lockfile")] = False,
    offline: Annotated[bool, typer.Option("--offline")] = False,
) -> None:
    """Lockfile ile mevcut ortamı eşitler (lock + install)."""
    try:
        with ui.spinner("Ortam eşitleniyor..."):
            operations.sync(frozen=frozen, offline=offline)
        ui.success("Ortam lockfile ile eşitlendi.")
    except exceptions.FrozenLockfileError as exc:
        ui.print_error_panel("Frozen Lockfile", str(exc))
        raise typer.Exit(code=1)
    except exceptions.PaketciError as exc:
        ui.print_error_panel("Hata", str(exc))
        raise typer.Exit(code=1)
