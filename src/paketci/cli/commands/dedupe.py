"""Dedupe komutu — lockfile'daki paket sürümlerinin çakışmasız ve tekilleştirilmiş olduğunu denetler."""

from __future__ import annotations

import sys
from typing import Annotated

import typer
from rich import print as rprint
from rich.table import Table

from paketci.core import operations
from paketci.core.exceptions import PaketciError


def dedupe_cmd(
    check: Annotated[
        bool,
        typer.Option(
            "--check",
            "-c",
            help="Sadece çakışma ve çoklu sürüm denetimi yapar; çakışma varsa 1 ile çıkar.",
        ),
    ] = False,
) -> None:
    """Bağımlılık grafiğinde tek sürüm (deduplication) ve kısıtlama uyumunu denetler."""
    try:
        result = operations.dedupe(check_only=check)
    except PaketciError as e:
        rprint(f"[bold red]Hata:[/] {e}")
        raise typer.Exit(code=1)

    if result.packages_checked == 0:
        rprint("[yellow]Lockfile boş veya paket bulunamadı.[/]")
        return

    table = Table(title="📦 Bağımlılık Tekilleştirme & Kısıtlama Uyumu (Dedupe)", show_header=True)
    table.add_column("Paket", style="bold cyan")
    table.add_column("Kilitli Sürüm", style="green")
    table.add_column("Tüketiciler (Dependents)", style="dim")
    table.add_column("Durum", justify="center")

    for rep in result.reports:
        dependents_str = ", ".join(f"{s} ({c})" for s, c in rep.dependents[:3])
        if len(rep.dependents) > 3:
            dependents_str += f" +{len(rep.dependents)-3}"
        if not dependents_str:
            dependents_str = "(bağımsız)"

        if rep.is_compatible:
            status = "[bold green]✔ Uyumlu[/]"
        else:
            status = "[bold red]✖ Çakışma[/]"

        table.add_row(rep.package, rep.locked_version, dependents_str, status)

    rprint(table)

    if result.conflict_count > 0:
        rprint(f"\n[bold red]✖ {result.conflict_count} pakette kısıtlama çakışması tespit edildi![/]")
        for rep in result.reports:
            if not rep.is_compatible:
                rprint(f"  [red]• {rep.package}:[/]")
                for conf in rep.conflicts:
                    rprint(f"    - {conf}")
        if check:
            raise typer.Exit(code=1)
    else:
        rprint(
            f"\n[bold green]✔ Tüm paketler ({result.compatible_count}/{result.packages_checked}) tekilleştirilmiş ve kısıtlamalarla tam uyumlu.[/]"
        )
