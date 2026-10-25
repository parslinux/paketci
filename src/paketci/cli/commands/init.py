"""init komutu — paketci init [name]"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Optional

import typer

from paketci.cli import ui
from paketci.core import exceptions, operations

app = typer.Typer()


@app.command("init")
def init_cmd(
    name: Annotated[
        Optional[str],
        typer.Argument(help="Proje adı (varsayılan: mevcut dizin adı)"),
    ] = None,
    venv: Annotated[
        bool,
        typer.Option("--venv", help="Otomatik .venv sanal ortamı oluştur"),
    ] = False,
    python: Annotated[
        str,
        typer.Option("--python", help="Python sürüm kısıtı (örn. '>=3.11')"),
    ] = ">=3.10",
) -> None:
    """Yeni bir Python projesi başlatır (pyproject.toml, README.md, .gitignore)."""
    try:
        pyproject_path = operations.init(
            name=name,
            requires_python=python,
            create_venv=venv,
        )
        ui.success(f"Proje başarıyla başlatıldı: [bold]{pyproject_path.parent.name}[/]")
        ui.info(f"Oluşturulan dosya: {pyproject_path.name}")
        if venv:
            ui.info("Sanal ortam (.venv) hazırlandı.")
    except exceptions.PaketciError as exc:
        ui.print_error_panel("Başlatma Hatası", str(exc))
        raise typer.Exit(code=1)
