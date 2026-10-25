"""Disk + bellek metadata önbelleği."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Optional

from filelock import FileLock

from paketci.index.models import PackageMetadata, ReleaseFile
from paketci.utils.paths import get_metadata_cache_dir
from paketci.utils.logging import get_logger

logger = get_logger(__name__)

# Saniye cinsinden TTL: 1 saat
DEFAULT_TTL = 3600


class MetadataCache:
    """İki katmanlı metadata önbelleği: bellek (dict) + disk (JSON dosyaları)."""

    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        ttl: int = DEFAULT_TTL,
    ) -> None:
        self._dir = cache_dir or get_metadata_cache_dir()
        self._ttl = ttl
        self._memory: dict[str, PackageMetadata] = {}

    @property
    def cache_dir(self) -> Path:
        return self._dir

    # ─── Okuma ───────────────────────────────────────────────────────────────

    def get(self, name: str, version: str) -> Optional[PackageMetadata]:
        """Önce bellekten, sonra diskten okur. Geçersiz TTL'de None döner."""
        key = _cache_key(name, version)

        # 1. Bellek
        if key in self._memory:
            return self._memory[key]

        # 2. Disk
        meta = self._load_from_disk(key)
        if meta:
            self._memory[key] = meta
        return meta

    # ─── Yazma ───────────────────────────────────────────────────────────────

    def set(self, meta: PackageMetadata) -> None:
        """Metadata'yı hem belleğe hem diske yazar."""
        key = _cache_key(meta.name, meta.version)
        self._memory[key] = meta
        self._save_to_disk(key, meta)

    def invalidate(self, name: str, version: str) -> None:
        key = _cache_key(name, version)
        self._memory.pop(key, None)
        path = self._path(key)
        if path.exists():
            path.unlink()

    # ─── Disk I/O ────────────────────────────────────────────────────────────

    def _path(self, key: str) -> Path:
        return self._dir / f"{key}.json"

    def _load_from_disk(self, key: str) -> Optional[PackageMetadata]:
        path = self._path(key)
        if not path.is_file():
            return None
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            ts: float = raw.get("_ts", 0)
            if time.time() - ts > self._ttl:
                logger.debug("Önbellek süresi doldu: %s", key)
                return None
            return _deserialize(raw)
        except Exception as exc:
            logger.debug("Önbellek okunamadı %s: %s", key, exc)
            return None

    def _save_to_disk(self, key: str, meta: PackageMetadata) -> None:
        path = self._path(key)
        lock_path = path.with_suffix(".lock")
        try:
            with FileLock(str(lock_path)):
                data = _serialize(meta)
                data["_ts"] = time.time()
                path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        except Exception as exc:
            logger.debug("Önbellek yazılamadı %s: %s", key, exc)


# ─── Serileştirme yardımcıları ────────────────────────────────────────────────

def _cache_key(name: str, version: str) -> str:
    safe_name = name.lower().replace("-", "_")
    safe_ver = version.replace("!", "_")
    return f"{safe_name}_{safe_ver}"


def _serialize(meta: PackageMetadata) -> dict:
    return {
        "name": meta.name,
        "version": meta.version,
        "requires_python": meta.requires_python,
        "requires_dist": meta.requires_dist,
        "files": [
            {
                "filename": f.filename,
                "url": f.url,
                "sha256": f.sha256,
                "size": f.size,
                "python_version": f.python_version,
                "requires_python": f.requires_python,
                "packagetype": f.packagetype,
                "yanked": f.yanked,
            }
            for f in meta.files
        ],
    }


def _deserialize(data: dict) -> PackageMetadata:
    files = [
        ReleaseFile(
            filename=f["filename"],
            url=f["url"],
            sha256=f["sha256"],
            size=f.get("size", 0),
            python_version=f.get("python_version", ""),
            requires_python=f.get("requires_python", ""),
            packagetype=f.get("packagetype", ""),
            yanked=f.get("yanked", False),
        )
        for f in data.get("files", [])
    ]
    return PackageMetadata(
        name=data["name"],
        version=data["version"],
        requires_python=data.get("requires_python", ""),
        requires_dist=data.get("requires_dist", []),
        files=files,
    )
