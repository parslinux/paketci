"""resolvelib AbstractReporter implementasyonu — çakışmaları raporlar."""

from __future__ import annotations

from resolvelib.reporters import BaseReporter

from paketci.utils.logging import get_logger

logger = get_logger(__name__)


class PaketciReporter(BaseReporter):
    """
    Çözümleme sürecinde kullanıcıya ilerleme ve çakışma bilgisi verir.
    CLI katmanı buradan rich tabanlı mesajlar üretebilir.
    """

    def starting(self) -> None:
        logger.debug("Bağımlılık çözümleme başladı.")

    def starting_round(self, index: int) -> None:
        logger.debug("Çözümleme turu: %d", index)

    def ending_round(self, index: int, state) -> None:
        resolved = len(state.mapping)
        logger.debug("Tur %d bitti — %d paket çözüldü.", index, resolved)

    def ending(self, state) -> None:
        logger.debug("Çözümleme tamamlandı: %d paket.", len(state.mapping))

    def adding_requirement(self, requirement, parent) -> None:
        parent_str = f" (kaynak: {parent[0]}=={parent[1]})" if parent else " (kök)"
        logger.debug("Gereksinim eklendi: %s%s", requirement, parent_str)

    def backtracking(self, cause) -> None:
        logger.warning(
            "[bold yellow]⚠ Geri izleme:[/] %s — çakışma tespit edildi, alternatif deneniyor.",
            cause,
        )

    def pinning(self, candidate) -> None:
        name, version = candidate
        logger.info("  [green]✔[/] %s==%s", name, version)
