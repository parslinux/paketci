"""Dizin ve dosya yolu yönetim yardımcıları."""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from platformdirs import user_cache_dir, user_config_dir

APP_NAME = "paketci"
APP_AUTHOR = "paketci"


def get_cache_dir() -> Path:
    """Paketci ana önbellek dizinini döndürür."""
    cache_path = Path(user_cache_dir(appname=APP_NAME, appauthor=APP_AUTHOR))
    cache_path.mkdir(parents=True, exist_ok=True)
    return cache_path


def get_metadata_cache_dir() -> Path:
    """PyPI metadata JSON önbellek dizini."""
    path = get_cache_dir() / "metadata"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_wheel_store_dir() -> Path:
    """Content-addressable wheel deposu dizini."""
    path = get_cache_dir() / "wheels"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_config_dir() -> Path:
    """Kullanıcı yapılandırma dizini."""
    config_path = Path(user_config_dir(appname=APP_NAME, appauthor=APP_AUTHOR))
    config_path.mkdir(parents=True, exist_ok=True)
    return config_path


def find_project_root(start_path: Path | None = None) -> Path:
    """Mevcut dizinden yukarı doğru giderek pyproject.toml veya paketci.lock içeren kök dizini bulur."""
    current = (start_path or Path.cwd()).resolve()
    for parent in [current, *current.parents]:
        if (parent / "pyproject.toml").is_file() or (parent / "paketci.lock").is_file():
            return parent
    return current


def link_or_copy(src: Path, dst: Path) -> None:
    """Önce hardlink dener; izin veya farklı dosya sistemi hatası olursa kopyalar (copy2)."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        dst.unlink()

    try:
        os.link(src, dst)
    except (OSError, NotImplementedError):
        shutil.copy2(src, dst)
