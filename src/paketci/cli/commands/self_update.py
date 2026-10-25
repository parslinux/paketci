"""self-update komutu — paketci self-update"""

from __future__ import annotations

from typing import Annotated, Optional

import typer
from rich import print as rprint

from paketci.core import self_update as core_update
from paketci.core.exceptions import PaketciError


def self_update_cmd(
    check_only: Annotated[
        bool,
        typer.Option(
            "--check",
            "-c",
            help="Yalnızca yeni sürüm olup olmadığını denetler, güncelleme yapmaz.",
        ),
    ] = False,
    version: Annotated[
        Optional[str],
        typer.Option(
            "--version",
            help="Belirtilen sürüme günceller / indirger.",
        ),
    ] = None,
) -> None:
    """paketci aracını en yeni sürüme günceller."""
    rprint("[cyan]🔍 paketci güncellemeleri kontrol ediliyor...[/]")
    try:
        check_res = core_update.check_for_updates()
    except Exception as e:
        rprint(f"[yellow]Güncelleme kontrolü yapılamadı: {e}[/]")
        return

    if not check_res.is_outdated and not version:
        rprint(f"[bold green]✔ paketci zaten en güncel sürümde:[/] [cyan]v{check_res.current_version}[/]")
        return

    target = version or check_res.latest_version
    rprint(
        f"[bold yellow]📦 Yeni sürüm mevcut:[/] [dim]v{check_res.current_version}[/] ➔ [bold green]v{target}[/]"
    )

    if check_res.release_notes:
        rprint("\n[bold]Sürüm Notları:[/]")
        rprint(f"[dim]{check_res.release_notes[:300]}[/]")

    if check_only:
        rprint("\n[dim]Güncellemek için 'paketci self-update' çalıştırabilirsiniz.[/]")
        return

    rprint(f"\n[cyan]🚀 paketci v{target} sürümüne güncelleniyor...[/]")
    try:
        core_update.perform_update(target_version=target)
        rprint(f"[bold green]✔ paketci başarıyla v{target} sürümüne güncellendi![/]")
    except PaketciError as exc:
        rprint(f"[bold red]Hata:[/] {exc}")
        raise typer.Exit(code=1)
