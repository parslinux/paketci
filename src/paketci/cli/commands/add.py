"""add komutu — paketci add <paket> [paket2 ...]"""

from __future__ import annotations

from typing import Annotated, Optional

import typer

from paketci.cli import ui
from paketci.core import exceptions, operations

app = typer.Typer()


@app.command("add")
def add_cmd(
    packages: Annotated[list[str], typer.Argument(help="Eklenecek paket(ler), PEP 508 formatında")],
    dev: Annotated[bool, typer.Option("--dev", "-d", help="[tool.paketci.dev] grubuna ekle")] = False,
    group: Annotated[Optional[str], typer.Option("--group", "-g", help="İsteğe bağlı bağımlılık grubu")] = None,
    offline: Annotated[bool, typer.Option("--offline", help="Önbellekten kur, ağa çıkma")] = False,
) -> None:
    """Projeye bağımlılık ekler, çözümler ve kurar."""
    try:
        with ui.spinner(f"Ekleniyor: {', '.join(packages)}..."):
            operations.add(
                packages=packages,
                dev=dev,
                optional_group=group,
                offline=offline,
            )
        ui.success(f"{len(packages)} paket eklendi ve kuruldu.")
        for pkg in packages:
            ui.console.print(f"  [package]{pkg}[/]")
    except exceptions.PaketciError as exc:
        ui.print_error_panel("Hata", str(exc))
        raise typer.Exit(code=1)
