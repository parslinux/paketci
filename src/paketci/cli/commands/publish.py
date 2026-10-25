"""publish komutu — paketci publish"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Optional

import typer

from paketci.cli import ui
from paketci.core import exceptions, operations

app = typer.Typer()


@app.command("publish")
def publish_cmd(
    repository: Annotated[
        str,
        typer.Option("--repository-url", "-r", help="Hedef PyPI upload endpoint adresi"),
    ] = "https://upload.pypi.org/legacy/",
    testpypi: Annotated[
        bool,
        typer.Option("--testpypi", help="TestPyPI deposuna yükle (https://test.pypi.org/legacy/)"),
    ] = False,
    token: Annotated[
        Optional[str],
        typer.Option("--token", "-t", help="PyPI API erişim belirteci (token)"),
    ] = None,
    dist: Annotated[
        Optional[Path],
        typer.Option("--dist", "-d", help="Yüklenecek paketlerin bulunduğu dizin (varsayılan: dist/)"),
    ] = None,
    skip_existing: Annotated[
        bool,
        typer.Option("--skip-existing", help="Paket depoda zaten varsa hata verme, atla"),
    ] = False,
) -> None:
    """Derlenmiş paketleri PyPI veya özel bir depoya yükler."""
    repo_url = "https://test.pypi.org/legacy/" if testpypi else repository
    try:
        uploaded = operations.publish_package(
            dist_dir=dist,
            repository_url=repo_url,
            token=token,
            skip_existing=skip_existing,
        )
        ui.success(f"Yayınlama başarılı! {len(uploaded)} dosya yüklendi:")
        for name in uploaded:
            ui.info(f"  🚀 {name}")
    except exceptions.PaketciError as exc:
        ui.print_error_panel("Yayınlama Hatası", str(exc))
        raise typer.Exit(code=1)
    except Exception as exc:
        ui.print_error_panel("Yayınlama Hatası", f"Beklenmeyen ağ/yükleme hatası: {exc}")
        raise typer.Exit(code=1)
