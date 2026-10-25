"""Typer root app — tüm komutları birleştirir."""

from __future__ import annotations

from typing import Annotated, Optional

import typer
from rich import print as rprint

from paketci import __version__
from paketci.cli.commands import (
    add,
    audit,
    build,
    cache,
    check,
    completion,
    dedupe,
    export,
    init,
    install,
    licenses,
    list,
    lock,
    outdated,
    publish,
    remove,
    run,
    sync,
    tree,
    update,
    why,
    workspace,
)
from paketci.utils.logging import setup_logging

# ─── Ana uygulama ─────────────────────────────────────────────────────────────

app = typer.Typer(
    name="paketci",
    help="📦 [bold cyan]paketci[/] — Modern, hızlı ve güvenilir Python paket yöneticisi.",
    rich_markup_mode="rich",
    no_args_is_help=True,
    pretty_exceptions_enable=True,
    pretty_exceptions_show_locals=False,
)

# Alt komutları kaydet
app.command("init")(init.init_cmd)
app.command("add")(add.add_cmd)
app.command("remove")(remove.remove_cmd)
app.command("install")(install.install_cmd)
app.command("lock")(lock.lock_cmd)
app.command("sync")(sync.sync_cmd)
app.command("update")(update.update_cmd)
app.command("list")(list.list_cmd)
app.command("tree")(tree.tree_cmd)
app.command("why")(why.why_cmd)
app.command("check")(check.check_cmd)
app.command("audit")(audit.audit_cmd)
app.command("export")(export.export_cmd)
app.command("outdated")(outdated.outdated_cmd)
app.command("licenses")(licenses.licenses_cmd)
app.command("dedupe")(dedupe.dedupe_cmd)
app.add_typer(workspace.app, name="workspace")
app.add_typer(cache.app, name="cache")
app.command("build")(build.build_cmd)
app.command("publish")(publish.publish_cmd)
app.command("completion")(completion.completion_cmd)
app.command(
    "run",
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)(run.run_cmd)


# ─── Global callback (--verbose, --version) ───────────────────────────────────

@app.callback(invoke_without_command=True)
def main_callback(
    ctx: typer.Context,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Detaylı çıktı")] = False,
    quiet: Annotated[bool, typer.Option("--quiet", "-q", help="Sadece hataları göster")] = False,
    version: Annotated[bool, typer.Option("--version", help="Versiyon bilgisi")] = False,
) -> None:
    setup_logging(verbose=verbose, quiet=quiet)
    if version:
        rprint(f"[bold]paketci[/] [cyan]{__version__}[/]")
        raise typer.Exit()


def main() -> None:
    """CLI giriş noktası."""
    app()


if __name__ == "__main__":
    main()
