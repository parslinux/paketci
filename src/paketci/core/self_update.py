"""Kendini güncelleme (self-update) operasyonu."""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from typing import Optional

import httpx
from packaging.version import parse as parse_version

from paketci import __version__
from paketci.core.exceptions import PaketciError


@dataclass
class VersionCheckResult:
    current_version: str
    latest_version: str
    is_outdated: bool
    release_notes: str = ""


def check_for_updates(repo: str = "parslinux/paketci") -> VersionCheckResult:
    """GitHub API ve PyPI üzerinden en güncel sürümü denetler."""
    latest_version = __version__
    release_notes = ""

    # 1. GitHub Releases dene
    try:
        url = f"https://api.github.com/repos/{repo}/releases/latest"
        resp = httpx.get(url, timeout=10.0, headers={"User-Agent": f"paketci/{__version__}"})
        if resp.status_code == 200:
            data = resp.json()
            tag = data.get("tag_name", "").lstrip("v")
            if tag:
                latest_version = tag
                release_notes = data.get("body", "")
    except Exception:
        pass

    # 2. PyPI fallback dene
    if latest_version == __version__:
        try:
            pypi_url = "https://pypi.org/pypi/paketci/json"
            resp = httpx.get(pypi_url, timeout=10.0)
            if resp.status_code == 200:
                data = resp.json()
                latest_version = data.get("info", {}).get("version", __version__)
        except Exception:
            pass

    cur_v = parse_version(__version__)
    lat_v = parse_version(latest_version)
    is_outdated = lat_v > cur_v

    return VersionCheckResult(
        current_version=__version__,
        latest_version=latest_version,
        is_outdated=is_outdated,
        release_notes=release_notes,
    )


def perform_update(target_version: Optional[str] = None) -> bool:
    """paketci paketini pip veya git üzerinden günceller."""
    pkg_spec = f"paketci=={target_version}" if target_version else "paketci"
    cmd = [sys.executable, "-m", "pip", "install", "--upgrade", pkg_spec]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise PaketciError(f"Güncelleme başarısız oldu:\n{res.stderr or res.stdout}")
    return True
