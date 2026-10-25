"""Lockfile dışa aktarma (export) modülü — requirements.txt üretir."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from paketci import __version__
from paketci.core.exceptions import PaketciError
from paketci.lockfile import io as lockfile_io
from paketci.utils.paths import find_project_root


def export_requirements(
    project_root: Optional[Path] = None,
    include_hashes: bool = True,
) -> str:
    """paketci.lock içeriğini standart pip requirements.txt formatına dönüştürür."""
    root = project_root or find_project_root()
    lock_path = root / "paketci.lock"
    if not lock_path.is_file():
        raise PaketciError("paketci.lock bulunamadı. Önce 'paketci lock' çalıştırın.")

    graph = lockfile_io.read(lock_path)
    lines = [
        f"# Bu dosya paketci v{__version__} tarafından paketci.lock dosyasından üretilmiştir.",
        "# Elle düzenlemeyiniz.",
        "",
    ]

    for pkg_name, pkg in sorted(graph.packages.items()):
        line = f"{pkg.name}=={pkg.version}"
        if include_hashes and pkg.files:
            hashes = [f"    --hash=sha256:{f.sha256}" for f in pkg.files if f.sha256]
            if hashes:
                line += " \\\n" + " \\\n".join(hashes)
        lines.append(line)

    return "\n".join(lines) + "\n"
