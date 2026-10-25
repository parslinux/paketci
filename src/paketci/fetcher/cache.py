"""Content-addressable wheel deposu (global önbellek)."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from paketci.utils.paths import get_wheel_store_dir, link_or_copy
from paketci.utils.logging import get_logger

logger = get_logger(__name__)


class WheelStore:
    """
    İndirilen wheel/sdist dosyalarını SHA-256 içeriğine göre global önbellekte saklar.
    Aynı dosya farklı projelerce hardlink (veya kopya) ile paylaşılır.
    """

    def __init__(self, store_dir: Optional[Path] = None) -> None:
        self._store = store_dir or get_wheel_store_dir()

    @property
    def store_dir(self) -> Path:
        return self._store

    @property
    def cache_dir(self) -> Path:
        return self._store

    def _store_path(self, sha256: str, filename: str) -> Path:
        """Önbellekteki dosya yolu: <store>/<sha256[:2]>/<sha256>/<filename>"""
        prefix = sha256[:2]
        return self._store / prefix / sha256 / filename

    def has(self, sha256: str, filename: str) -> bool:
        return self._store_path(sha256, filename).is_file()

    def get(self, sha256: str, filename: str) -> Optional[Path]:
        path = self._store_path(sha256, filename)
        return path if path.is_file() else None

    def put(self, src: Path, sha256: str) -> Path:
        """
        İndirilen dosyayı depoya taşır ve depo yolunu döndürür.
        Dosya zaten varsa sessizce atlar.
        """
        dest = self._store_path(sha256, src.name)
        if dest.is_file():
            logger.debug("Önbellekte zaten var: %s", dest.name)
            return dest
        dest.parent.mkdir(parents=True, exist_ok=True)
        link_or_copy(src, dest)
        logger.debug("Önbelleğe alındı: %s", dest.name)
        return dest

    def link_to(self, sha256: str, filename: str, target_dir: Path) -> Optional[Path]:
        """Önbellekteki dosyayı hedef dizine hardlink/kopya ile bağlar."""
        src = self.get(sha256, filename)
        if src is None:
            return None
        dst = target_dir / filename
        link_or_copy(src, dst)
        return dst
