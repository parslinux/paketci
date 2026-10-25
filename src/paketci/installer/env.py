"""Hedef ortam (venv / site-packages) tespiti."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from paketci.core.exceptions import EnvironmentError as PaketciEnvError
from paketci.utils.logging import get_logger

logger = get_logger(__name__)


class TargetEnv:
    """Kurulumun yapılacağı Python ortamı."""

    def __init__(
        self,
        python: Path,
        site_packages: Path,
        scripts_dir: Path,
    ) -> None:
        self.python = python
        self.site_packages = site_packages
        self.scripts_dir = scripts_dir

    def get_installed_packages(self) -> dict[str, str]:
        """Hedef ortamda kurulu paketlerin {canonical_name: version} sözlüğünü döndürür."""
        import importlib.metadata
        from packaging.utils import canonicalize_name

        installed: dict[str, str] = {}
        if not self.site_packages.is_dir():
            return installed

        try:
            dists = importlib.metadata.distributions(path=[str(self.site_packages)])
            for dist in dists:
                raw_name = dist.metadata.get("Name")
                version = dist.metadata.get("Version")
                if raw_name:
                    installed[canonicalize_name(raw_name)] = version or ""
        except Exception as exc:
            logger.debug("Kurulu paketler taranırken hata: %s", exc)

        return installed

    def is_installed(self, name: str, version: Optional[str] = None) -> bool:
        """Paketin (ve varsa versiyonunun) ortamda kurulu olup olmadığını kontrol eder."""
        from packaging.utils import canonicalize_name
        pkgs = self.get_installed_packages()
        norm_name = canonicalize_name(name)
        if norm_name not in pkgs:
            return False
        if version is not None:
            return pkgs[norm_name] == version
        return True

    def __repr__(self) -> str:
        return f"<TargetEnv site_packages={self.site_packages}>"


def detect_env(target: Optional[Path] = None) -> TargetEnv:
    """
    Hedef ortamı tespit eder.

    Priority:
    1. ``target`` argümanı belirtilmişse orayı kullan (--target desteği).
    2. Aktif sanal ortam (VIRTUAL_ENV / .venv) varsa onu kullan.
    3. Mevcut Python yorumlayıcısının site-packages'ini kullan.

    Raises:
        PaketciEnvError: site-packages dizini bulunamazsa.
    """
    import os

    # 1. Açık --target
    if target:
        target = target.resolve()
        target.mkdir(parents=True, exist_ok=True)
        return TargetEnv(
            python=Path(sys.executable),
            site_packages=target,
            scripts_dir=target / "bin",
        )

    # 2. VIRTUAL_ENV ortam değişkeni
    venv_env = os.environ.get("VIRTUAL_ENV")
    if venv_env:
        return _from_venv(Path(venv_env))

    # 3. Proje kökündeki .venv
    cwd = Path.cwd()
    local_venv = cwd / ".venv"
    if local_venv.is_dir():
        return _from_venv(local_venv)

    # 4. Mevcut Python yorumlayıcısı
    return _from_interpreter(Path(sys.executable))


def _from_venv(venv_path: Path) -> TargetEnv:
    import sysconfig, subprocess, json

    python = venv_path / "bin" / "python"
    if not python.is_file():
        python = venv_path / "bin" / "python3"
    if not python.is_file():
        raise PaketciEnvError(f"Python yorumlayıcısı bulunamadı: {venv_path / 'bin'}")

    site_packages = _get_site_packages(python)
    scripts_dir = venv_path / "bin"
    logger.debug("Ortam tespit edildi (venv): %s", site_packages)
    return TargetEnv(python=python, site_packages=site_packages, scripts_dir=scripts_dir)


def _from_interpreter(python: Path) -> TargetEnv:
    site_packages = _get_site_packages(python)
    scripts_dir = python.parent
    logger.debug("Ortam tespit edildi (sistem): %s", site_packages)
    return TargetEnv(python=python, site_packages=site_packages, scripts_dir=scripts_dir)


def _get_site_packages(python: Path) -> Path:
    import subprocess, json

    code = (
        "import json, sysconfig; "
        "print(json.dumps(sysconfig.get_paths()))"
    )
    try:
        out = subprocess.check_output([str(python), "-c", code], text=True)
        paths = json.loads(out)
        sp = paths.get("purelib") or paths.get("platlib")
        if sp:
            return Path(sp)
    except Exception as exc:
        raise PaketciEnvError(f"site-packages tespit edilemedi: {exc}") from exc

    raise PaketciEnvError("site-packages dizini bulunamadı.")
