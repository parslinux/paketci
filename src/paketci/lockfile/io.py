"""Lockfile JSON okuma ve yazma."""

from __future__ import annotations

import json
from pathlib import Path

from paketci import __version__
from paketci.lockfile.models import LockedFile, LockedGraph, LockedPackage
from paketci.core.exceptions import LockfileError
from paketci.utils.logging import get_logger

logger = get_logger(__name__)

LOCKFILE_VERSION = 1


def write(graph: LockedGraph, path: Path) -> None:
    """LockedGraph'ı JSON lockfile olarak diske yazar."""
    data: dict = {
        "lockfileVersion": LOCKFILE_VERSION,
        "generatedBy": f"paketci {__version__}",
        "python": graph.python,
        "packages": {},
    }

    for name, pkg in sorted(graph.packages.items()):
        data["packages"][name] = {
            "version": pkg.version,
            "files": [
                {"filename": f.filename, "url": f.url, "sha256": f.sha256}
                for f in pkg.files
            ],
            "dependencies": pkg.dependencies,
        }

    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.debug("Lockfile yazıldı: %s", path)


def read(path: Path) -> LockedGraph:
    """JSON lockfile'ı okur ve LockedGraph döndürür."""
    if not path.is_file():
        raise LockfileError(f"Lockfile bulunamadı: {path}")

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise LockfileError(f"Lockfile ayrıştırılamadı: {exc}") from exc

    version = data.get("lockfileVersion", 1)
    if version != LOCKFILE_VERSION:
        raise LockfileError(
            f"Lockfile versiyonu uyumsuz: beklenen {LOCKFILE_VERSION}, bulunan {version}"
        )

    packages: dict[str, LockedPackage] = {}
    for name, entry in data.get("packages", {}).items():
        files = [
            LockedFile(
                filename=f["filename"],
                url=f["url"],
                sha256=f["sha256"],
            )
            for f in entry.get("files", [])
        ]
        packages[name] = LockedPackage(
            name=name,
            version=entry["version"],
            files=files,
            dependencies=entry.get("dependencies", []),
        )

    return LockedGraph(
        lockfile_version=version,
        generated_by=data.get("generatedBy", ""),
        python=data.get("python", ""),
        packages=packages,
    )
