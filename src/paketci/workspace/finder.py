"""Workspace keşif ve üye çözümleme fonksiyonları."""

from __future__ import annotations

import glob
from pathlib import Path
from typing import Optional

from paketci.config.loader import ConfigLoader
from paketci.core.exceptions import ConfigError
from paketci.workspace.models import Workspace, WorkspaceMember


def find_workspace(project_root: Path) -> Optional[Workspace]:
    """Proje kökündeki [tool.paketci.workspace] tanımlarını bulur ve Workspace döndürür."""
    loader = ConfigLoader(project_root)
    try:
        config = loader.load()
    except ConfigError:
        return None

    if not config.workspace_members:
        return None

    members: list[WorkspaceMember] = []
    seen_paths: set[Path] = set()

    for pattern in config.workspace_members:
        # Glob pattern eşleşmelerini kök dizine göre çöz
        match_paths = sorted(project_root.glob(pattern))
        for p in match_paths:
            if p.is_dir() and (p / "pyproject.toml").is_file():
                resolved_p = p.resolve()
                if resolved_p in seen_paths:
                    continue
                seen_paths.add(resolved_p)

                try:
                    sub_loader = ConfigLoader(p)
                    sub_config = sub_loader.load()
                    pkg_name = sub_config.name or p.name
                    members.append(
                        WorkspaceMember(
                            name=pkg_name,
                            version=sub_config.version,
                            path=p,
                            config=sub_config,
                        )
                    )
                except ConfigError:
                    continue

    return Workspace(root=project_root, config=config, members=members)
