"""Git (VCS) ve yerel dizin (Path / Editable) bağımlılık işleyicisi."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional, Tuple

import platformdirs

from paketci.core.exceptions import PaketciError
from paketci.installer.env import TargetEnv


def get_vcs_cache_dir() -> Path:
    base = platformdirs.user_cache_path("paketci") / "vcs"
    base.mkdir(parents=True, exist_ok=True)
    return base


def is_git_url(url: str) -> bool:
    """Verilen stringin bir git URL'si olup olmadığını denetler."""
    return url.startswith(("git+", "git://")) or (url.startswith("https://") and url.endswith(".git"))


def clone_git_repo(git_url: str, ref: Optional[str] = None) -> Path:
    """Git deposunu klonlar veya günceller; klonlanmış dizini döner."""
    clean_url = git_url
    if clean_url.startswith("git+"):
        clean_url = clean_url[4:]

    # Depo adını URL'den çıkar
    repo_name = clean_url.rstrip("/").split("/")[-1]
    if repo_name.endswith(".git"):
        repo_name = repo_name[:-4]

    target_dir = get_vcs_cache_dir() / repo_name

    if (target_dir / ".git").is_dir():
        # Zaten varsa güncelle
        subprocess.run(["git", "fetch", "--depth", "1"], cwd=target_dir, capture_output=True)
        if ref:
            subprocess.run(["git", "checkout", ref], cwd=target_dir, capture_output=True)
        else:
            subprocess.run(["git", "reset", "--hard", "FETCH_HEAD"], cwd=target_dir, capture_output=True)
    else:
        cmd = ["git", "clone", "--depth", "1"]
        if ref:
            cmd.extend(["--branch", ref])
        cmd.extend([clean_url, str(target_dir)])
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            raise PaketciError(f"Git deposu klonlanamadı: {clean_url}\n{res.stderr}")

    return target_dir


def install_editable(source_dir: Path, env: TargetEnv) -> str:
    """Bir paketi hedef ortama geliştirme modunda (editable / .pth) bağlar."""
    resolved_source = source_dir.resolve()
    if not (resolved_source / "pyproject.toml").is_file() and not (resolved_source / "setup.py").is_file():
        raise PaketciError(f"Geçersiz Python paketi (pyproject.toml veya setup.py bulunamadı): {source_dir}")

    # Paket adını bul
    pkg_name = resolved_source.name
    try:
        from paketci.config.loader import ConfigLoader
        cfg = ConfigLoader(resolved_source).load()
        if cfg.name:
            pkg_name = cfg.name
    except Exception:
        pass

    site_packages = env.site_packages
    if not site_packages.is_dir():
        site_packages.mkdir(parents=True, exist_ok=True)

    # .pth dosyası oluştur (örn: my_pkg.pth -> /path/to/src)
    pth_file = site_packages / f"__paketci_editable__{pkg_name}.pth"
    src_subdir = resolved_source / "src"
    target_path = src_subdir if src_subdir.is_dir() else resolved_source
    pth_file.write_text(str(target_path) + "\n", encoding="utf-8")

    # .dist-info minimal kaydı oluştur (importlib.metadata için)
    dist_info_dir = site_packages / f"{pkg_name}-0.0.0.dist-info"
    dist_info_dir.mkdir(parents=True, exist_ok=True)
    (dist_info_dir / "METADATA").write_text(
        f"Metadata-Version: 2.1\nName: {pkg_name}\nVersion: 0.0.0.dev0\n",
        encoding="utf-8",
    )
    (dist_info_dir / "INSTALLER").write_text("paketci-editable\n", encoding="utf-8")

    return pkg_name
