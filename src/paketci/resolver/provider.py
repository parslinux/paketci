"""resolvelib AbstractProvider implementasyonu — sync httpx kullanır."""

from __future__ import annotations

import re
from typing import Iterator, Optional

from packaging.requirements import Requirement
from packaging.version import Version, InvalidVersion
from resolvelib.providers import AbstractProvider

from paketci.index.cache import MetadataCache
from paketci.index.client import PyPIClient
from paketci.index.models import PackageMetadata
from paketci.utils.logging import get_logger

logger = get_logger(__name__)


class PaketciProvider(AbstractProvider):
    """
    resolvelib için AbstractProvider implementasyonu.

    Sync httpx.Client kullanır; resolvelib'in sync callback'leriyle
    event loop çakışması olmaz.
    """

    def __init__(
        self,
        requirements: list[str],
        client: PyPIClient,
        cache: MetadataCache,
    ) -> None:
        self._root_reqs: list[Requirement] = [Requirement(r) for r in requirements]
        self._client = client
        self._cache = cache

    # ─── resolvelib hook'ları ─────────────────────────────────────────────────

    def identify(self, requirement_or_candidate) -> str:
        """Gereksinim veya adayı normalize edilmiş paket adına indirger."""
        if isinstance(requirement_or_candidate, Requirement):
            return _normalize(requirement_or_candidate.name)
        # Candidate tuple: (name, version)
        return _normalize(requirement_or_candidate[0])

    def get_preference(self, identifier, resolutions, candidates, information, backtrack_causes):
        """Çözümleme önceliğini belirler — daha az aday = önce çöz."""
        return sum(1 for _ in candidates[identifier])

    def find_matches(self, identifier, requirements, incompatibilities):
        """identifier için geçerli versiyon adaylarını üretir."""
        reqs = list(requirements[identifier])
        bad_versions = {v for v, _ in incompatibilities[identifier]}

        versions = self._get_versions(identifier)

        for version in versions:
            if version in bad_versions:
                continue
            candidate = (identifier, version)
            if all(self._matches_req(req, candidate) for req in reqs):
                yield candidate

    def is_satisfied_by(self, requirement, candidate) -> bool:
        """Aday, gereksinimi karşılıyor mu?"""
        return self._matches_req(requirement, candidate)

    def get_dependencies(self, candidate) -> list[Requirement]:
        """Adayın bağımlılıklarını döndürür."""
        name, version = candidate
        meta = self._fetch_metadata(name, version)
        deps = []
        for dep_str in (meta.requires_dist or []):
            try:
                req = Requirement(dep_str)
                # Koşullu bağımlılıkları şimdilik platform için evaluate et
                if req.marker is None or req.marker.evaluate():
                    deps.append(req)
            except Exception as exc:
                logger.debug("Bağımlılık ayrıştırılamadı '%s': %s", dep_str, exc)
        return deps

    # ─── İç yardımcılar ──────────────────────────────────────────────────────

    def _get_versions(self, name: str) -> list[str]:
        """PyPI'dan versiyon listesini çeker (önce cache'e bak, sonra ağ)."""
        try:
            versions = self._client.get_versions(name)
            # Geçersiz version string'lerini filtrele
            valid = []
            for v in versions:
                try:
                    Version(v)
                    valid.append(v)
                except InvalidVersion:
                    pass
            return sorted(valid, key=Version, reverse=True)
        except Exception as exc:
            logger.warning("Versiyon listesi alınamadı '%s': %s", name, exc)
            return []

    def _fetch_metadata(self, name: str, version: str) -> PackageMetadata:
        """Metadata'yı önce disk cache'ten, yoksa PyPI'dan getirir."""
        cached = self._cache.get(name, version)
        if cached:
            return cached

        meta = self._client.get_metadata(name, version)
        self._cache.set(meta)
        return meta

    def _matches_req(self, req: Requirement, candidate: tuple[str, str]) -> bool:
        _, version = candidate
        if not req.specifier:
            return True
        try:
            return req.specifier.contains(version, prereleases=False)
        except Exception:
            return False


def _normalize(name: str) -> str:
    """Paket adını normalize et (PEP 503)."""
    return re.sub(r"[-_.]+", "-", name).lower()
