"""Wheel kurulum wrapper — `installer` kütüphanesi."""

from __future__ import annotations

from pathlib import Path

from installer import install
from installer.destinations import SchemeDictionaryDestination
from installer.sources import WheelFile

from paketci.core.exceptions import InstallError
from paketci.installer.env import TargetEnv
from paketci.utils.logging import get_logger

logger = get_logger(__name__)


def install_wheel(wheel_path: Path, env: TargetEnv) -> None:
    """
    Wheel dosyasını hedef ortama kurar.

    Args:
        wheel_path: .whl dosyasının yerel yolu.
        env: Hedef kurulum ortamı.

    Raises:
        InstallError: Kurulum başarısız olursa.
    """
    if not wheel_path.is_file():
        raise InstallError(f"Wheel dosyası bulunamadı: {wheel_path}")

    import sysconfig
    import sys

    # installer kütüphanesi için scheme dict'ini oluştur
    scheme = {
        "scripts": str(env.scripts_dir),
        "purelib": str(env.site_packages),
        "platlib": str(env.site_packages),
        "headers": str(env.site_packages.parent / "include"),
        "data": str(env.site_packages.parent),
    }

    logger.info("  📦 Kuruluyor: %s", wheel_path.name)

    script_kind = "winshell" if sys.platform == "win32" else "posix"
    try:
        destination = SchemeDictionaryDestination(
            scheme_dict=scheme,
            interpreter=str(env.python),
            script_kind=script_kind,
            overwrite_existing=True,
        )
        with WheelFile.open(wheel_path) as source:
            install(source, destination, {})
    except Exception as exc:
        raise InstallError(f"Wheel kurulamadı '{wheel_path.name}': {exc}") from exc

    logger.info("  ✅ Kuruldu: %s", wheel_path.stem)
