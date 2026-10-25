"""Yapılandırma veri modelleri — ProjectConfig, Dependency."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Dependency:
    """pyproject.toml'daki tek bir bağımlılık girişi."""

    name: str
    constraint: str = ""  # örn. ">=2.0,<3"
    extras: list[str] = field(default_factory=list)

    def pep508(self) -> str:
        """PEP 508 formatında string döndürür: 'requests[security]>=2.0'"""
        extras_str = f"[{','.join(self.extras)}]" if self.extras else ""
        return f"{self.name}{extras_str}{self.constraint}"

    def __str__(self) -> str:
        return self.pep508()


@dataclass
class ProjectConfig:
    """pyproject.toml [project] + [tool.paketci] bölümünü temsil eder."""

    name: str = ""
    version: str = "0.1.0"
    requires_python: str = ""
    dependencies: list[Dependency] = field(default_factory=list)
    optional_dependencies: dict[str, list[Dependency]] = field(default_factory=dict)

    # [tool.paketci] özel ayarları
    lockfile_path: str = "paketci.lock"
    index_url: str = "https://pypi.org/simple"
    extra_index_urls: list[str] = field(default_factory=list)
    trusted_hosts: list[str] = field(default_factory=list)
    workspace_members: list[str] = field(default_factory=list)
    peer_dependencies: dict[str, str] = field(default_factory=dict)
