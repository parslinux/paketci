"""licenses komutu — paketci licenses"""

from __future__ import annotations

import typer
from rich.table import Table

from paketci.cli import ui
from paketci.core import exceptions, operations

app = typer.Typer()


@app.command("licenses")
def licenses_cmd() -> None:
    """Projede kullanılan paketlerin lisans bilgilerini listeler."""
    try:
        items = operations.get_licenses()
        if not items:
            ui.info("Hiç paket bulunamadı (lockfile boş veya yok).")
            return

        table = Table(title=f"📜 Bağımlılık Lisansları ({len(items)})", show_header=True)
        table.add_column("Paket", style="bold cyan")
        table.add_column("Sürüm", style="dim")
        table.add_column("Lisans", style="bold green")

        for item in items:
            table.add_row(item.name, item.version, item.license_name)

        ui.console.print(table)
    except exceptions.PaketciError as exc:
        ui.print_error_panel("Lisans Tarama Hatası", str(exc))
        raise typer.Exit(code=1)
