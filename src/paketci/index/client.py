"""PyPI JSON API istemcisi — sync ve async versiyonlar."""

from __future__ import annotations

from typing import Optional

import httpx

from paketci.core.exceptions import FetchError
from paketci.index.models import PackageMetadata, ReleaseFile
from paketci.utils.logging import get_logger

logger = get_logger(__name__)

PYPI_BASE = "https://pypi.org/pypi"
DEFAULT_TIMEOUT = 30.0


# ─── Sync İstemci (resolver tarafından kullanılır) ───────────────────────────

class PyPIClient:
    """
    Sync PyPI JSON API istemcisi.

    Resolver, resolvelib'in sync callback'leri içinden çağırır;
    bu yüzden sync httpx.Client kullanmak zorunludur.
    Büyük paralel indirmeler için Downloader'daki async httpx kullanılır.
    """

    def __init__(
        self,
        base_url: str = PYPI_BASE,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._client: Optional[httpx.Client] = None

    def __enter__(self) -> "PyPIClient":
        self._client = httpx.Client(timeout=self._timeout)
        return self

    def __exit__(self, *args: object) -> None:
        if self._client:
            self._client.close()
            self._client = None

    # ─── Public API ──────────────────────────────────────────────────────────

    def get_metadata(self, name: str, version: Optional[str] = None) -> PackageMetadata:
        """Belirli bir paket (ve isteğe bağlı versiyon) için metadata getirir."""
        url = (
            f"{self._base_url}/{name}/{version}/json"
            if version
            else f"{self._base_url}/{name}/json"
        )
        data = self._get_json(url)
        return _parse_pypi_json(data)

    def get_versions(self, name: str) -> list[str]:
        """PyPI'daki tüm versiyonları döndürür (en yeni önce)."""
        url = f"{self._base_url}/{name}/json"
        data = self._get_json(url)
        releases = data.get("releases", {})
        # Yanked olmayan versiyonları filtrele
        valid = []
        for ver, files in releases.items():
            if files and not all(f.get("yanked", False) for f in files):
                valid.append(ver)
        return sorted(valid, reverse=True)

    # ─── Internal ────────────────────────────────────────────────────────────

    def _get_json(self, url: str) -> dict:
        assert self._client is not None, "İstemci başlatılmadı — 'with' bloğu kullanın"
        try:
            resp = self._client.get(url)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                raise FetchError(f"Paket bulunamadı: {url}") from exc
            raise FetchError(f"PyPI API hatası: {exc.response.status_code} — {url}") from exc
        except httpx.RequestError as exc:
            raise FetchError(f"Ağ hatası: {exc}") from exc


# ─── Async İstemci (downloader tarafından kullanılır) ────────────────────────

class AsyncPyPIClient:
    """
    Async PyPI JSON API istemcisi.
    Sadece Downloader ve metadata ön-fetch için kullanılır.
    """

    def __init__(
        self,
        base_url: str = PYPI_BASE,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self) -> "AsyncPyPIClient":
        self._client = httpx.AsyncClient(timeout=self._timeout)
        return self

    async def __aexit__(self, *args: object) -> None:
        if self._client:
            await self._client.aclose()

    async def get_metadata(self, name: str, version: Optional[str] = None) -> PackageMetadata:
        url = (
            f"{self._base_url}/{name}/{version}/json"
            if version
            else f"{self._base_url}/{name}/json"
        )
        data = await self._get_json(url)
        return _parse_pypi_json(data)

    async def _get_json(self, url: str) -> dict:
        assert self._client is not None
        try:
            resp = await self._client.get(url)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                raise FetchError(f"Paket bulunamadı: {url}") from exc
            raise FetchError(f"PyPI API hatası: {exc.response.status_code}") from exc
        except httpx.RequestError as exc:
            raise FetchError(f"Ağ hatası: {exc}") from exc


# ─── JSON Parse ──────────────────────────────────────────────────────────────

def _parse_pypi_json(data: dict) -> PackageMetadata:
    info = data.get("info", {})
    version = info.get("version", "")
    urls: list[dict] = data.get("urls", [])
    files = [_parse_file(u) for u in urls]

    return PackageMetadata(
        name=info.get("name", ""),
        version=version,
        requires_python=info.get("requires_python") or "",
        requires_dist=info.get("requires_dist") or [],
        files=files,
    )


def _parse_file(url_entry: dict) -> ReleaseFile:
    digests = url_entry.get("digests", {})
    return ReleaseFile(
        filename=url_entry.get("filename", ""),
        url=url_entry.get("url", ""),
        sha256=digests.get("sha256", ""),
        size=url_entry.get("size", 0),
        python_version=url_entry.get("python_version", ""),
        requires_python=url_entry.get("requires_python") or "",
        packagetype=url_entry.get("packagetype", ""),
        yanked=bool(url_entry.get("yanked", False)),
    )
