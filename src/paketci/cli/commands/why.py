"""why komutu — paketci why <paket>"""

from __future__ import annotations

from typing import Annotated

import typer
from rich.tree import Tree

from paketci.cli import ui
from paketci.core import exceptions, operations

app = typer.Typer()


@app.command("why")
def why_cmd(
    package: Annotated[str, typer.Argument(help="Sorgulanacak paket adı")],
) -> None:
    """Bir paketin neden bağımlılık ağacında olduğunu açıklar."""
    try:
        result = operations.why(package)
        if not result:
            ui.warn(f"'{package}' bağımlılık ağacında bulunamadı.")
            return

        tree = Tree(f"[bold cyan]{package}[/] neden kurulu?")
        for depender, reqs in result.items():
            branch = tree.add(f"[package]{depender}[/] bunu istiyor:")
            for req in reqs:
                branch.add(f"[dim]{req}[/]")

        ui.console.print(tree)
    except exceptions.PaketciError as exc:
        ui.print_error_panel("Hata", str(exc))
        raise typer.Exit(code=1)
