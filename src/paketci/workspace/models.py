"""Workspace (Monorepo) modelleri ve veri yapıları."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from paketci.config.models import ProjectConfig


@dataclass
class WorkspaceMember:
    """Çalışma alanındaki tek bir alt proje/paket."""

    name: str
    version: str
    path: Path
    config: ProjectConfig

    @property
    def rel_path(self) -> str:
        return self.path.name


@dataclass
class Workspace:
    """Çoklu paket barındıran kök çalışma alanı."""

    root: Path
    config: ProjectConfig
    members: list[WorkspaceMember] = field(default_factory=list)

    def get_member(self, name: str) -> WorkspaceMember | None:
        name_lower = name.lower()
        for member in self.members:
            if member.name.lower() == name_lower:
                return member
        return None
