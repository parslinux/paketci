"""lock komutu — paketci lock"""

from __future__ import annotations

from typing import Annotated

import typer

from paketci.cli import ui
from paketci.core import exceptions, operations

app = typer.Typer()


@app.command("lock")
def lock_cmd(
    offline: Annotated[bool, typer.Option("--offline")] = False,
) -> None:
    """pyproject.toml'u okuyup lockfile oluşturur/günceller."""
    try:
        with ui.spinner("Bağımlılıklar çözümleniyor..."):
            operations.lock(offline=offline)
        ui.success("paketci.lock güncellendi.")
    except exceptions.ResolveError as exc:
        ui.print_error_panel("Çözümleme Hatası", str(exc))
        raise typer.Exit(code=1)
    except exceptions.PaketciError as exc:
        ui.print_error_panel("Hata", str(exc))
        raise typer.Exit(code=1)
