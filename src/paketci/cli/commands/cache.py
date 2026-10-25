"""cache komutu — paketci cache [info|clean]"""

from __future__ import annotations

import typer
from rich.table import Table

from paketci.cli import ui
from paketci.core import exceptions, operations

app = typer.Typer(help="Önbellek (cache) yönetimi komutları.")


def _format_size(size_bytes: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


@app.command("info")
def info_cmd() -> None:
    """Önbellek konumu ve boyut istatistiklerini görüntüler."""
    try:
        report = operations.cache_info()

        table = Table(title="📦 Paketci Önbellek Bilgisi", show_header=True)
        table.add_column("Önbellek Türü", style="bold cyan")
        table.add_column("Dizin", style="dim")
        table.add_column("Dosya Sayısı", justify="right")
        table.add_column("Boyut", justify="right", style="green")

        table.add_row(
            "Wheel Deposu (İndirilen paketler)",
            str(report.wheel_cache_dir),
            str(report.wheel_count),
            _format_size(report.wheel_size_bytes),
        )
        table.add_row(
            "Metadata Önbelleği (PyPI JSON)",
            str(report.metadata_cache_dir),
            str(report.metadata_count),
            _format_size(report.metadata_size_bytes),
        )
        table.add_section()
        table.add_row(
            "[bold]Toplam[/]",
            "",
            str(report.wheel_count + report.metadata_count),
            f"[bold green]{_format_size(report.total_size_bytes)}[/]",
        )

        ui.console.print(table)
    except exceptions.PaketciError as exc:
        ui.print_error_panel("Önbellek Hatası", str(exc))
        raise typer.Exit(code=1)


@app.command("clean")
def clean_cmd() -> None:
    """Tüm paket ve metadata önbelleğini temizler."""
    try:
        count, size = operations.cache_clean()
        ui.success(f"Önbellek temizlendi! {count} dosya silindi ({_format_size(size)} boşaltıldı).")
    except exceptions.PaketciError as exc:
        ui.print_error_panel("Temizleme Hatası", str(exc))
        raise typer.Exit(code=1)
