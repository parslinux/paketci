"""add komutu — paketci add <paket> [paket2 ...]"""

from __future__ import annotations

from typing import Annotated, Optional

import typer

from paketci.cli import ui
from paketci.core import exceptions, operations

app = typer.Typer()


@app.command("add")
def add_cmd(
    packages: Annotated[list[str], typer.Argument(help="Eklenecek paket(ler), PEP 508 formatında, yerel dizin veya Git URL'si")],
    dev: Annotated[bool, typer.Option("--dev", "-d", help="[project.optional-dependencies.dev] grubuna ekle")] = False,
    group: Annotated[Optional[str], typer.Option("--group", "-g", help="İsteğe bağlı bağımlılık grubu")] = None,
    offline: Annotated[bool, typer.Option("--offline", help="Önbellekten kur, ağa çıkma")] = False,
    editable: Annotated[bool, typer.Option("--editable", "-e", help="Yerel paketi geliştirme modunda bağla")] = False,
) -> None:
    """Projeye bağımlılık (PyPI, yerel dizin veya Git) ekler ve kurar."""
    try:
        with ui.spinner(f"Ekleniyor: {', '.join(packages)}..."):
            operations.add(
                packages=packages,
                dev=dev,
                optional_group=group,
                offline=offline,
                editable=editable,
            )
        ui.success(f"{len(packages)} paket eklendi ve kuruldu.")
        for pkg in packages:
            ui.console.print(f"  [package]{pkg}[/]")
    except exceptions.PaketciError as exc:
        ui.print_error_panel("Hata", str(exc))
        raise typer.Exit(code=1)
