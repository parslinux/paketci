from __future__ import annotations

from typing import Annotated

import typer
from rich.table import Table

from paketci.cli import ui
from paketci.core import exceptions, operations

app = typer.Typer()


@app.command("outdated")
def outdated_cmd(
    pre: Annotated[
        bool,
        typer.Option("--pre", help="Kararsız ve pre-release sürümleri de dahil et"),
    ] = False,
) -> None:
    """Kilitli paketlerin PyPI'daki daha yeni sürümlerini denetler."""
    try:
        with ui.spinner("PyPI'daki en son sürümler taranıyor..."):
            items = operations.find_outdated(include_prereleases=pre)

        if not items:
            ui.success("Tüm paketler en güncel sürümlerinde! 🎉")
            return

        table = Table(title=f"📦 Güncellenebilecek Paketler ({len(items)})", show_header=True)
        table.add_column("Paket", style="bold cyan")
        table.add_column("Mevcut Sürüm", style="dim")
        table.add_column("En Yeni Sürüm", style="bold green")
        table.add_column("Tür", justify="center")

        type_styles = {
            "major": "[bold red]MAJOR[/]",
            "minor": "[yellow]MINOR[/]",
            "patch": "[green]PATCH[/]",
        }

        for item in items:
            type_str = type_styles.get(item.update_type, item.update_type)
            table.add_row(item.name, item.current_version, item.latest_version, type_str)

        ui.console.print(table)
        ui.info("Tüm paketleri güncellemek için: 'paketci update'")
    except exceptions.PaketciError as exc:
        ui.print_error_panel("Sürüm Kontrol Hatası", str(exc))
        raise typer.Exit(code=1)
