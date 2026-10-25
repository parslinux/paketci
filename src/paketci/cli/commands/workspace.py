"""Workspace (Monorepo) CLI komutları."""

from __future__ import annotations

import sys
from typing import Annotated, Optional

import typer
from rich import print as rprint
from rich.table import Table

from paketci.core import operations
from paketci.core.exceptions import PaketciError

app = typer.Typer(
    help="🏢 [bold cyan]workspace[/] — Çoklu paket (monorepo) çalışma alanı yönetimi.",
    rich_markup_mode="rich",
)


@app.command("list")
def workspace_list_cmd() -> None:
    """Çalışma alanındaki (workspace) tüm üye paketleri listeler."""
    try:
        ws = operations.list_workspace()
    except PaketciError as e:
        rprint(f"[bold red]Hata:[/] {e}")
        raise typer.Exit(code=1)

    table = Table(title=f"🏢 Workspace Üyeleri ({len(ws.members)} paket)", show_header=True)
    table.add_column("Paket Adı", style="bold cyan")
    table.add_column("Sürüm", style="green")
    table.add_column("Dizin", style="dim")
    table.add_column("Bağımlılıklar", justify="right")

    for member in ws.members:
        dep_count = len(member.config.dependencies)
        table.add_row(
            member.name,
            member.version,
            str(member.path.relative_to(ws.root)),
            f"{dep_count} adet",
        )

    rprint(table)


@app.command(
    "run",
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)
def workspace_run_cmd(
    ctx: typer.Context,
    member: Annotated[
        Optional[str],
        typer.Option("--member", "-m", help="Yalnızca belirtilen üye pakette çalıştır."),
    ] = None,
) -> None:
    """Workspace üyelerinde belirtilen komutu çalıştırır."""
    if not ctx.args:
        rprint("[bold red]Hata:[/] Çalıştırılacak bir komut belirtmelisiniz. Örnek: 'paketci workspace run pytest'")
        raise typer.Exit(code=1)

    cmd = list(ctx.args)
    try:
        results = operations.run_workspace_cmd(command=cmd, member_name=member)
    except PaketciError as e:
        rprint(f"[bold red]Hata:[/] {e}")
        raise typer.Exit(code=1)

    failed = [name for name, code in results.items() if code != 0]
    if failed:
        rprint(f"[bold red]✖ Komut {len(failed)} üyede başarısız oldu:[/] {', '.join(failed)}")
        raise typer.Exit(code=1)
    else:
        rprint(f"[bold green]✔ Komut tüm üyelerde ({len(results)}) başarıyla tamamlandı.[/]")
