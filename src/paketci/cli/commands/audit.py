"""Audit komutu — paketci audit (Güvenlik zafiyeti tarayıcısı)."""

from __future__ import annotations

import sys
from typing import Annotated

import typer
from rich import print as rprint
from rich.table import Table

from paketci.core import audit as core_audit
from paketci.core.exceptions import PaketciError


def audit_cmd(
    strict: Annotated[
        bool,
        typer.Option(
            "--strict",
            "-s",
            help="Herhangi bir güvenlik açığı bulunması durumunda çıkış kodu 1 (exit 1) ile sonlandırır (CI için).",
        ),
    ] = False,
) -> None:
    """Projedeki kilitli paketleri bilinen güvenlik zafiyetlerine (CVE / GHSA) karşı tarar."""
    rprint("[cyan]🔍 Güvenlik zafiyetleri taranıyor (OSV.dev / PyPA Advisory DB)...[/]")
    try:
        result = core_audit.audit()
    except PaketciError as exc:
        rprint(f"[bold red]Hata:[/] {exc}")
        raise typer.Exit(code=1)

    if not result.has_vulnerabilities:
        rprint(
            f"[bold green]✔ {result.packages_scanned} paket tarandı — Bilinen herhangi bir güvenlik açığı bulunamadı![/]"
        )
        return

    table = Table(
        title=f"🚨 Güvenlik Zafiyetleri ({len(result.vulnerabilities)} bulgu tespit edildi)",
        show_header=True,
    )
    table.add_column("Paket", style="bold cyan")
    table.add_column("Kurulu", style="dim")
    table.add_column("Kimlik (ID)", style="bold")
    table.add_column("Şiddet", justify="center")
    table.add_column("Düzeltilen Sürüm", style="green")
    table.add_column("Özet", style="white")

    for v in result.vulnerabilities:
        sev = v.severity.upper()
        if "CRITICAL" in sev:
            sev_styled = "[bold white on red] KRİTİK [/]"
        elif "HIGH" in sev:
            sev_styled = "[bold red] YÜKSEK [/]"
        elif "MODERATE" in sev or "MEDIUM" in sev:
            sev_styled = "[bold yellow] ORTA [/]"
        else:
            sev_styled = "[bold blue] DÜŞÜK [/]"

        fixed_str = ", ".join(v.fixed_in) if v.fixed_in else "[dim]Bilinmiyor[/]"
        table.add_row(
            v.package,
            v.version,
            f"[link={v.reference_url}]{v.id}[/link]",
            sev_styled,
            fixed_str,
            v.summary[:70] + ("..." if len(v.summary) > 70 else ""),
        )

    rprint(table)
    rprint(f"\n[bold red]✖ Toplam {len(result.vulnerabilities)} güvenlik zafiyeti tespit edildi![/]")

    if strict:
        raise typer.Exit(code=1)
