"""build komutu — paketci build"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Optional

import typer

from paketci.cli import ui
from paketci.core import exceptions, operations

app = typer.Typer()


@app.command("build")
def build_cmd(
    sdist: Annotated[bool, typer.Option("--sdist/--no-sdist", help="Source distribution (.tar.gz) derle")] = True,
    wheel: Annotated[bool, typer.Option("--wheel/--no-wheel", help="Binary wheel (.whl) derle")] = True,
    dest: Annotated[
        Optional[Path],
        typer.Option("--dest", "-d", help="Çıktı dizini (varsayılan: dist/)"),
    ] = None,
) -> None:
    """Projeyi PEP 517 standardına uygun wheel ve sdist formatlarına derler."""
    try:
        built = operations.build_package(sdist=sdist, wheel=wheel, dest_dir=dest)
        ui.success(f"Derleme tamamlandı! {len(built)} paket oluşturuldu:")
        for path in built:
            ui.info(f"  📦 {path.name}")
    except exceptions.PaketciError as exc:
        ui.print_error_panel("Derleme Hatası", str(exc))
        raise typer.Exit(code=1)
    except Exception as exc:
        ui.print_error_panel("Derleme Hatası", f"Beklenmeyen hata: {exc}")
        raise typer.Exit(code=1)
