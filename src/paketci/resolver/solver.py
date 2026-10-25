"""resolvelib orkestrasyonu — solver ana giriş noktası."""

from __future__ import annotations

from packaging.requirements import Requirement
from resolvelib import Resolver, ResolutionImpossible

from paketci.core.exceptions import ResolveError
from paketci.index.cache import MetadataCache
from paketci.index.client import PyPIClient
from paketci.resolver.provider import PaketciProvider
from paketci.resolver.reporter import PaketciReporter
from paketci.utils.logging import get_logger

logger = get_logger(__name__)


class SolveResult:
    """Başarılı çözümlemenin sonucu."""

    def __init__(self, mapping: dict[str, tuple[str, str]]) -> None:
        # mapping: {normalize_name: (name, version)}
        self.mapping = mapping

    def resolved_packages(self) -> list[tuple[str, str]]:
        """(name, version) listesini döndürür."""
        return list(self.mapping.values())

    def __repr__(self) -> str:
        return f"<SolveResult packages={len(self.mapping)}>"


def solve(
    requirements: list[str],
    client: PyPIClient,
    cache: MetadataCache,
    max_rounds: int = 100,
    solver_type: str = "resolvelib",
) -> SolveResult:
    """
    Verilen gereksinimler için bağımlılık grafiğini çözer.

    Args:
        requirements: PEP 508 formatında gereksinim stringleri.
        client: Sync PyPI istemcisi (with bloğu içinde açık olmalı).
        cache: Metadata önbelleği.
        max_rounds: resolvelib maksimum tur sayısı.
        solver_type: 'resolvelib' veya 'sat' (Native DPLL).

    Returns:
        SolveResult — çözülmüş paket versiyonları.

    Raises:
        ResolveError: Çözüm bulunamazsa.
    """
    if solver_type == "sat":
        from paketci.resolver.sat_solver import solve_with_sat
        return solve_with_sat(requirements, client, cache)

    provider = PaketciProvider(
        requirements=requirements,
        client=client,
        cache=cache,
    )
    reporter = PaketciReporter()
    resolver = Resolver(provider, reporter)

    parsed_reqs = []
    for r in requirements:
        try:
            parsed_reqs.append(Requirement(r))
        except Exception as exc:
            raise ResolveError(f"Geçersiz gereksinim '{r}': {exc}") from exc

    try:
        result = resolver.resolve(parsed_reqs, max_rounds=max_rounds)
    except ResolutionImpossible as exc:
        causes = _format_causes(exc.causes)
        raise ResolveError(f"Bağımlılık çözümlenemedi:\n{causes}") from exc

    mapping: dict[str, tuple[str, str]] = {}
    for norm_name, candidate in result.mapping.items():
        # candidate = (norm_name, version) tuple
        name, version = candidate
        mapping[norm_name] = (name, version)

    return SolveResult(mapping=mapping)


def _format_causes(causes) -> str:
    lines = []
    for cause in causes:
        lines.append(f"  • {cause.requirement} (kaynak: {cause.parent})")
    return "\n".join(lines) if lines else "  (detay yok)"
