"""list komutu — paketci list"""

from __future__ import annotations

import typer

from paketci.cli import ui
from paketci.core import exceptions, operations

app = typer.Typer()


@app.command("list")
def list_cmd() -> None:
    """Lockfile'daki tüm paketleri tablo olarak listeler."""
    try:
        pkgs = operations.list_packages()
        if not pkgs:
            ui.info("Hiç paket yok (lockfile bulunamadı veya boş).")
            return

        rows = [(p.name, p.version, "") for p in pkgs]
        tbl = ui.make_package_table(rows, title=f"Paketler ({len(pkgs)})")
        ui.console.print(tbl)
    except exceptions.PaketciError as exc:
        ui.print_error_panel("Hata", str(exc))
        raise typer.Exit(code=1)
