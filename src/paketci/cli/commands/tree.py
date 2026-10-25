"""tree komutu — paketci tree"""

from __future__ import annotations

import typer
from rich.tree import Tree

from paketci.cli import ui
from paketci.core import exceptions, operations

app = typer.Typer()


@app.command("tree")
def tree_cmd() -> None:
    """Projenin tüm bağımlılıklarını hiyerarşik ağaç olarak listeler."""
    try:
        nodes = operations.dependency_tree()
        if not nodes:
            ui.info("Ağaçta görüntülenecek bağımlılık yok (lockfile boş veya bulunamadı).")
            return

        tree = Tree("📦 [bold cyan]Proje Bağımlılık Ağacı[/]")

        def _add_to_tree(parent_tree: Tree, node: operations.TreeNode) -> None:
            constraint_part = f" [dim]({node.constraint})[/]" if node.constraint else ""
            label = f"[bold green]{node.name}[/] [cyan]{node.version}[/]{constraint_part}"
            branch = parent_tree.add(label)
            for child in node.dependencies:
                _add_to_tree(branch, child)

        for root_node in nodes:
            _add_to_tree(tree, root_node)

        ui.console.print(tree)
    except exceptions.PaketciError as exc:
        ui.print_error_panel("Ağaç Hatası", str(exc))
        raise typer.Exit(code=1)
