"""Lockfile veri modelleri."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class LockedFile:
    """Lockfile'daki tek bir dağıtım dosyası kaydı."""

    filename: str
    url: str
    sha256: str


@dataclass
class LockedPackage:
    """Lockfile'daki tek bir paket kaydı."""

    name: str
    version: str
    files: list[LockedFile] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)  # PEP 508 stringleri

    @property
    def id(self) -> str:
        return f"{self.name}=={self.version}"


@dataclass
class LockedGraph:
    """Tüm lockfile içeriği."""

    lockfile_version: int = 1
    generated_by: str = ""
    python: str = ""
    packages: dict[str, LockedPackage] = field(default_factory=dict)
    # key: normalize edilmiş paket adı

    def get(self, name: str) -> Optional[LockedPackage]:
        from paketci.resolver.provider import _normalize
        return self.packages.get(_normalize(name))

    def all_packages(self) -> list[LockedPackage]:
        return list(self.packages.values())
