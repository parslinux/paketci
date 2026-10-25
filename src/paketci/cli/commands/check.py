"""check komutu — paketci check"""

from __future__ import annotations

import typer
from rich.table import Table

from paketci.cli import ui
from paketci.core import exceptions, operations

app = typer.Typer()


@app.command("check")
def check_cmd() -> None:
    """Projenin bağımlılık, lockfile ve sanal ortam sağlık durumunu denetler."""
    try:
        report = operations.check()

        if report.messages:
            for msg in report.messages:
                ui.warn(msg)

        if not report.pyproject_exists or not report.lockfile_exists:
            raise typer.Exit(code=1)

        if report.missing_in_lock:
            ui.warn(f"Lockfile'da eksik bağımlılıklar var: {', '.join(report.missing_in_lock)}")
            ui.info("Çözüm: 'paketci lock' komutunu çalıştırın.")

        if report.missing_in_env:
            table = Table(title="Sanal Ortamda Eksik Paketler", show_header=True)
            table.add_column("Paket", style="bold red")
            table.add_column("Kilitli Sürüm", style="yellow")
            for name, ver in report.missing_in_env:
                table.add_row(name, ver)
            ui.console.print(table)
            ui.info("Çözüm: 'paketci sync' veya 'paketci install' çalıştırarak ortamı güncelleyin.")

        if report.peer_warnings:
            table = Table(title="⚠ Peer Dependency Uyarıları", show_header=True)
            table.add_column("Uyarı / Açıklama", style="yellow")
            for warn in report.peer_warnings:
                table.add_row(warn)
            ui.console.print(table)

        if report.is_healthy:
            ui.success(
                f"Tüm bağımlılıklar sağlıklı! ({len(report.installed_ok)} paket sanal ortamda kurulu ve kilitli)"
            )
        else:
            raise typer.Exit(code=1)

    except exceptions.PaketciError as exc:
        ui.print_error_panel("Denetim Hatası", str(exc))
        raise typer.Exit(code=1)
