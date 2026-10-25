"""Python sürüm ve ortam yönetimi (Toolchain)."""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from paketci.core.exceptions import PaketciError
from paketci.utils.paths import find_project_root


@dataclass
class PythonInstallation:
    version: str
    executable: Path
    is_active: bool = False


def find_system_pythons() -> List[PythonInstallation]:
    """Sistemdeki tüm CPython / PyPy kurulumlarını tarar ve listeler."""
    found: List[PythonInstallation] = []
    seen_paths = set()

    # Taranacak standart python ikili adları
    names = [
        "python",
        "python3",
        "python3.14",
        "python3.13",
        "python3.12",
        "python3.11",
        "python3.10",
        "pypy3",
    ]

    active_exec = Path(os.sys.executable).resolve()

    for name in names:
        bin_path_str = shutil.which(name)
        if bin_path_str:
            p = Path(bin_path_str).resolve()
            if p in seen_paths:
                continue
            seen_paths.add(p)

            try:
                out = subprocess.check_output(
                    [str(p), "-c", "import platform; print(platform.python_version())"],
                    text=True,
                    timeout=2.0,
                ).strip()
                if out:
                    found.append(
                        PythonInstallation(
                            version=out,
                            executable=p,
                            is_active=(p == active_exec),
                        )
                    )
            except Exception:
                continue

    # Versiyona göre sırala
    found.sort(key=lambda x: x.version, reverse=True)
    return found


def pin_python_version(version: str, project_root: Optional[Path] = None) -> Path:
    """Proje köküne .python-version dosyası yazarak hedef sürümü sabitler."""
    root = project_root or find_project_root()
    target_file = root / ".python-version"
    target_file.write_text(version.strip() + "\n", encoding="utf-8")
    return target_file


def get_pinned_python_version(project_root: Optional[Path] = None) -> Optional[str]:
    """Projede sabitlenmiş (.python-version) Python sürümünü okur."""
    root = project_root or find_project_root()
    target_file = root / ".python-version"
    if target_file.is_file():
        return target_file.read_text(encoding="utf-8").strip()
    return None
