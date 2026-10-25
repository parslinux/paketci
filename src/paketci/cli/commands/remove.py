"""remove komutu — paketci remove <paket>"""

from __future__ import annotations

from typing import Annotated, Optional

import typer

from paketci.cli import ui
from paketci.core import exceptions, operations

app = typer.Typer()


@app.command("remove")
def remove_cmd(
    packages: Annotated[list[str], typer.Argument(help="Kaldırılacak paket(ler)")],
    group: Annotated[Optional[str], typer.Option("--group", "-g")] = None,
) -> None:
    """Projeden bağımlılık kaldırır ve lockfile'ı günceller."""
    try:
        with ui.spinner(f"Kaldırılıyor: {', '.join(packages)}..."):
            operations.remove(packages=packages, optional_group=group)
        ui.success(f"{len(packages)} paket kaldırıldı.")
    except exceptions.PaketciError as exc:
        ui.print_error_panel("Hata", str(exc))
        raise typer.Exit(code=1)
