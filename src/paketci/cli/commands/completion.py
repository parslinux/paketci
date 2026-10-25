"""Shell completion komutu — bash, zsh, fish tamamlama betiklerini üretir veya kurar."""

from __future__ import annotations

import sys
from enum import Enum
from typing import Annotated, Optional

import typer
from rich import print as rprint
from typer.completion import Shells, get_completion_script, install


class SupportedShell(str, Enum):
    bash = "bash"
    zsh = "zsh"
    fish = "fish"
    powershell = "powershell"
    pwsh = "pwsh"


def completion_cmd(
    shell: Annotated[
        Optional[SupportedShell],
        typer.Argument(
            help="Hedef kabuk türü (bash, zsh, fish, powershell, pwsh). Belirtilmezse mevcut kabuk algılanır.",
        ),
    ] = None,
    install_flag: Annotated[
        bool,
        typer.Option(
            "--install",
            "-i",
            help="Tamamlama betiğini doğrudan kabuk yapılandırma dosyasına (~/.bashrc, ~/.zshrc vb.) kurar.",
        ),
    ] = False,
) -> None:
    """Kabuk otomatik tamamlama (shell completion) betiğini üretir veya kurar."""
    shell_str = shell.value if shell else None

    if install_flag:
        try:
            installed_shell, path = install(
                shell=shell_str,
                prog_name="paketci",
                complete_var="_PAKETCI_COMPLETE",
            )
            rprint(f"[bold green]✓[/] [cyan]{installed_shell}[/] otomatik tamamlama betiği başarıyla kuruldu:")
            rprint(f"  [dim]{path}[/]")
            rprint("[dim]Değişikliklerin geçerli olması için terminalinizi yeniden başlatın veya yapılandırma dosyanızı 'source' edin.[/]")
        except Exception as e:
            rprint(f"[bold red]Hata:[/] Otomatik tamamlama betiği kurulamadı: {e}", file=sys.stderr)
            raise typer.Exit(code=1)
    else:
        target_shell = shell_str or "bash"
        try:
            script = get_completion_script(
                prog_name="paketci",
                complete_var="_PAKETCI_COMPLETE",
                shell=target_shell,
            )
            # Betiği ham çıktı olarak stdout'a bas (eval "$(paketci completion bash)" uyumu için)
            sys.stdout.write(script + "\n")
            sys.stdout.flush()
        except Exception as e:
            rprint(f"[bold red]Hata:[/] {target_shell} için tamamlama betiği üretilemedi: {e}", file=sys.stderr)
            raise typer.Exit(code=1)
