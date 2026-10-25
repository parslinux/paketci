"""PyPI API veri modelleri."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from packaging.version import Version


@dataclass
class ReleaseFile:
    """Tek bir dağıtım dosyası (wheel veya sdist)."""

    filename: str
    url: str
    sha256: str
    size: int = 0
    python_version: str = ""  # "py3", "cp311" vb.
    requires_python: str = ""
    packagetype: str = ""  # "bdist_wheel" | "sdist"
    yanked: bool = False

    @property
    def is_wheel(self) -> bool:
        return self.filename.endswith(".whl")

    @property
    def is_sdist(self) -> bool:
        return self.packagetype == "sdist" or self.filename.endswith((".tar.gz", ".zip"))


@dataclass
class PackageMetadata:
    """PyPI JSON API'den gelen bir paketin tam metadata'sı."""

    name: str
    version: str
    requires_python: str = ""
    requires_dist: list[str] = field(default_factory=list)
    files: list[ReleaseFile] = field(default_factory=list)

    @property
    def parsed_version(self) -> Version:
        return Version(self.version)

    def best_wheel(self, python_tag: str = "cp3", abi_tag: str = "", platform_tag: str = "any") -> Optional[ReleaseFile]:
        """Platform uyumlu en iyi wheel'i döndürür; yoksa None."""
        wheels = [f for f in self.files if f.is_wheel and not f.yanked]
        # Önce pure-python (none-any) tercih et
        for w in wheels:
            parts = w.filename.rstrip(".whl").rsplit("-", 3)
            if len(parts) >= 2 and parts[-1] == "any":
                return w
        # Aksi hâlde ilk wheel'i dön
        return wheels[0] if wheels else None

    def best_sdist(self) -> Optional[ReleaseFile]:
        sdists = [f for f in self.files if f.is_sdist and not f.yanked]
        return sdists[0] if sdists else None
