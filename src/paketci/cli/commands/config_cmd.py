"""config komutları — paketci config get/set/list/unset"""

from __future__ import annotations

from typing import Annotated, Optional

import typer
from rich import print as rprint
from rich.table import Table

from paketci.config.global_config import GlobalConfig

app = typer.Typer(
    help="⚙️ [bold cyan]config[/] — Küresel yapılandırma ve kimlik bilgisi yönetimi.",
    rich_markup_mode="rich",
)


@app.command("get")
def config_get(
    key: Annotated[str, typer.Argument(help="Okunacak anahtar (örn. index.default.token)")],
) -> None:
    """Küresel yapılandırmadan bir değeri okur."""
    cfg = GlobalConfig()
    val = cfg.get(key)
    if val is None:
        rprint(f"[dim]'{key}' için değer tanımlı değil.[/]")
        raise typer.Exit(code=1)
    # Maskeleme: Eğer anahtar 'token', 'secret', 'password' içeriyorsa maskeli göster
    if any(s in key.lower() for s in ("token", "secret", "password", "key")):
        masked = str(val)[:4] + "••••••••" + str(val)[-4:] if len(str(val)) > 8 else "••••••••"
        rprint(f"[bold cyan]{key}[/] = [yellow]{masked}[/]")
    else:
        rprint(f"[bold cyan]{key}[/] = [green]{val}[/]")


@app.command("set")
def config_set(
    key: Annotated[str, typer.Argument(help="Yazılacak anahtar (örn. index.default.url)")],
    value: Annotated[str, typer.Argument(help="Atanacak değer")],
) -> None:
    """Küresel yapılandırmaya yeni bir anahtar/değer kaydeder."""
    cfg = GlobalConfig()
    cfg.set(key, value)
    rprint(f"[bold green]✔[/] [cyan]{key}[/] kaydedildi.")


@app.command("unset")
def config_unset(
    key: Annotated[str, typer.Argument(help="Silinecek anahtar")],
) -> None:
    """Küresel yapılandırmadan bir anahtarı kaldırır."""
    cfg = GlobalConfig()
    ok = cfg.unset(key)
    if ok:
        rprint(f"[bold green]✔[/] [cyan]{key}[/] silindi.")
    else:
        rprint(f"[yellow]'{key}' anahtarı bulunamadı.[/]")


@app.command("list")
def config_list() -> None:
    """Tüm küresel yapılandırma girdilerini listeler."""
    cfg = GlobalConfig()
    items = cfg.list_all()
    if not items:
        rprint(f"[dim]Küresel yapılandırma boş: {cfg.path}[/]")
        return

    table = Table(title=f"⚙️ Küresel Yapılandırma ({cfg.path})", show_header=True)
    table.add_column("Anahtar", style="bold cyan")
    table.add_column("Değer", style="green")

    for k, v in sorted(items.items()):
        val_str = str(v)
        if any(s in k.lower() for s in ("token", "secret", "password", "key")):
            val_str = val_str[:4] + "••••••••" + val_str[-4:] if len(val_str) > 8 else "••••••••"
        table.add_row(k, val_str)

    rprint(table)


@app.command("path")
def config_path() -> None:
    """Küresel config.toml dosyasının dosya yolu konumunu ekrana basar."""
    cfg = GlobalConfig()
    rprint(f"[cyan]{cfg.path}[/]")
