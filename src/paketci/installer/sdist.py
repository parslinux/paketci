"""sdist → wheel build wrapper — `build` + `pyproject-hooks`."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from paketci.core.exceptions import InstallError
from paketci.utils.logging import get_logger

logger = get_logger(__name__)


def build_sdist_to_wheel(sdist_path: Path, build_dir: Path) -> Path:
    """
    Bir sdist'i wheel'e derler.

    Args:
        sdist_path: .tar.gz veya .zip sdist dosyası.
        build_dir: Oluşturulan wheel'in bırakılacağı dizin.

    Returns:
        Oluşturulan .whl dosyasının yolu.

    Raises:
        InstallError: Build başarısız olursa.
    """
    import tarfile, zipfile, tempfile

    build_dir.mkdir(parents=True, exist_ok=True)
    source_dir = build_dir / "source"
    source_dir.mkdir(exist_ok=True)

    logger.info("  🔨 sdist build ediliyor: %s", sdist_path.name)

    # Kaynak arşivi aç
    try:
        if sdist_path.name.endswith(".tar.gz"):
            with tarfile.open(sdist_path, "r:gz") as tf:
                tf.extractall(source_dir)
        elif sdist_path.name.endswith(".zip"):
            with zipfile.ZipFile(sdist_path) as zf:
                zf.extractall(source_dir)
        else:
            raise InstallError(f"Bilinmeyen sdist formatı: {sdist_path.name}")
    except Exception as exc:
        raise InstallError(f"sdist açılamadı: {exc}") from exc

    # Gerçek kaynak dizini (genellikle source_dir/<name>-<ver>/)
    children = list(source_dir.iterdir())
    real_source = children[0] if len(children) == 1 and children[0].is_dir() else source_dir

    # `build` CLI ile wheel üret
    cmd = [
        sys.executable, "-m", "build",
        "--wheel",
        "--outdir", str(build_dir),
        str(real_source),
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        raise InstallError(
            f"sdist build başarısız: {sdist_path.name}\n{exc.stderr}"
        ) from exc

    wheels = list(build_dir.glob("*.whl"))
    if not wheels:
        raise InstallError(f"Build sonrası wheel bulunamadı: {build_dir}")

    logger.info("  ✅ Build tamamlandı: %s", wheels[0].name)
    return wheels[0]
