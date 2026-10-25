"""update komutu — paketci update"""

from __future__ import annotations

from typing import Annotated, Optional

import typer

from paketci.cli import ui
from paketci.core import exceptions, operations

app = typer.Typer()


@app.command("update")
def update_cmd(
    packages: Annotated[Optional[list[str]], typer.Argument(help="Güncellenecek paket(ler); boşsa hepsini güncelle")] = None,
) -> None:
    """Paket(ler)i en yeni versiyona günceller ve lockfile'ı yeniler."""
    try:
        with ui.spinner("Güncelleniyor..."):
            operations.update(packages=packages)
        if packages:
            ui.success(f"Güncellendi: {', '.join(packages)}")
        else:
            ui.success("Tüm paketler güncellendi.")
    except exceptions.PaketciError as exc:
        ui.print_error_panel("Hata", str(exc))
        raise typer.Exit(code=1)
