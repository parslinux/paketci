"""python komutları — paketci python list/pin/which"""

from __future__ import annotations

from typing import Annotated, Optional

import typer
from rich import print as rprint
from rich.table import Table

from paketci.core import python_toolchain

app = typer.Typer(
    help="🐍 [bold cyan]python[/] — Python sürüm ve ortam yönetimi (Toolchain).",
    rich_markup_mode="rich",
)


@app.command("list")
def python_list() -> None:
    """Sistemde kurulu olan Python sürümlerini listeler."""
    pythons = python_toolchain.find_system_pythons()
    if not pythons:
        rprint("[yellow]Sistemde Python kurulumu tespit edilemedi.[/]")
        return

    pinned = python_toolchain.get_pinned_python_version()

    table = Table(title="🐍 Sistemde Tespit Edilen Python Sürümleri", show_header=True)
    table.add_column("Sürüm", style="bold cyan")
    table.add_column("Yol (Executable)", style="dim")
    table.add_column("Durum", justify="center")

    for py in pythons:
        status_parts = []
        if py.is_active:
            status_parts.append("[bold green]Aktif (.venv)[/]")
        if pinned and py.version.startswith(pinned):
            status_parts.append("[bold yellow]Sabitlenmiş (.python-version)[/]")

        status = " ".join(status_parts) if status_parts else "[dim]Kullanılabilir[/]"
        table.add_row(py.version, str(py.executable), status)

    rprint(table)


@app.command("pin")
def python_pin(
    version: Annotated[str, typer.Argument(help="Sabitlenecek Python sürümü (örn: 3.12 veya 3.11.8)")],
) -> None:
    """Proje köküne .python-version dosyası yazarak hedef Python sürümünü sabitler."""
    try:
        path = python_toolchain.pin_python_version(version)
        rprint(f"[bold green]✔[/] Proje Python sürümü [cyan]{version}[/] olarak sabitlendi: [dim]{path.name}[/]")
    except Exception as e:
        rprint(f"[bold red]Hata:[/] {e}")
        raise typer.Exit(code=1)


@app.command("which")
def python_which(
    version: Annotated[Optional[str], typer.Argument(help="İsteğe bağlı hedeflenen sürüm")] = None,
) -> None:
    """Aktif veya belirtilen Python sürümünün çalıştırılabilir dosya yolunu gösterir."""
    target_ver = version or python_toolchain.get_pinned_python_version()
    pythons = python_toolchain.find_system_pythons()

    if target_ver:
        matched = [p for p in pythons if p.version.startswith(target_ver)]
        if matched:
            rprint(str(matched[0].executable))
            return
        rprint(f"[bold red]Hata:[/] '{target_ver}' ile eşleşen Python sürümü bulunamadı.", file=typer.sys.stderr)
        raise typer.Exit(code=1)

    for p in pythons:
        if p.is_active:
            rprint(str(p.executable))
            return

    if pythons:
        rprint(str(pythons[0].executable))
    else:
        rprint("[bold red]Hata:[/] Python bulunamadı.", file=typer.sys.stderr)
        raise typer.Exit(code=1)
