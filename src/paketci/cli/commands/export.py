"""export komutu — paketci export"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich import print as rprint

from paketci.core import export as core_export
from paketci.core.exceptions import PaketciError


def export_cmd(
    output: Annotated[
        Optional[Path],
        typer.Option(
            "--output",
            "-o",
            help="Çıktının yazılacağı dosya yolu (örn. requirements.txt). Belirtilmezse stdout'a yazılır.",
        ),
    ] = None,
    hashes: Annotated[
        bool,
        typer.Option(
            "--hashes/--no-hashes",
            help="Deterministik kurulum için SHA-256 sağlama toplamı satırlarını dahil eder.",
        ),
    ] = True,
) -> None:
    """paketci.lock dosyasını standart requirements.txt formatında dışa aktarır."""
    try:
        content = core_export.export_requirements(include_hashes=hashes)
    except PaketciError as exc:
        rprint(f"[bold red]Hata:[/] {exc}", file=sys.stderr)
        raise typer.Exit(code=1)

    if output:
        output.write_text(content, encoding="utf-8")
        rprint(f"[bold green]✔[/] [cyan]{output}[/] başarıyla oluşturuldu.")
    else:
        sys.stdout.write(content)
        sys.stdout.flush()
