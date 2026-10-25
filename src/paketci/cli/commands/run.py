"""run komutu — paketci run <komut> [args]..."""

from __future__ import annotations

import sys
from typing import Annotated, List

import typer

from paketci.cli import ui
from paketci.core import exceptions, operations

app = typer.Typer()


@app.command(
    "run",
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)
def run_cmd(
    ctx: typer.Context,
    command: Annotated[
        str,
        typer.Argument(help="Çalıştırılacak komut (örn. 'python', 'pytest')"),
    ],
) -> None:
    """Proje sanal ortamı bağlamında bir komut veya betik çalıştırır."""
    full_cmd = [command] + ctx.args
    try:
        retcode = operations.run_cmd(full_cmd)
        if retcode != 0:
            raise typer.Exit(code=retcode)
    except exceptions.PaketciError as exc:
        ui.print_error_panel("Çalıştırma Hatası", str(exc))
        raise typer.Exit(code=1)
    except FileNotFoundError as exc:
        ui.print_error_panel("Komut Bulunamadı", f"'{command}' komutu bulunamadı: {exc}")
        raise typer.Exit(code=127)
