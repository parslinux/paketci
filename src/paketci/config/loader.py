"""pyproject.toml okuma/yazma — tomlkit ile yorumlar korunur."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

import tomlkit
from tomlkit.container import Container

from paketci.config.models import Dependency, ProjectConfig
from paketci.core.exceptions import ConfigError
from paketci.utils.paths import find_project_root


def _parse_dep(dep_str: str) -> Dependency:
    """'requests[security]>=2.0' gibi PEP 508 stringini Dependency nesnesine çevirir."""
    # Extras ayır
    extras: list[str] = []
    extras_match = re.search(r"\[([^\]]+)\]", dep_str)
    if extras_match:
        extras = [e.strip() for e in extras_match.group(1).split(",")]
        dep_str = dep_str[: extras_match.start()] + dep_str[extras_match.end() :]

    # Versiyon kısıtlamasını ayır
    constraint_match = re.search(r"(>=|<=|!=|~=|==|>|<)[^\s,;]+(?:,(?:>=|<=|!=|~=|==|>|<)[^\s,;]+)*", dep_str)
    constraint = constraint_match.group(0) if constraint_match else ""
    name = dep_str[: constraint_match.start()].strip() if constraint_match else dep_str.strip()

    return Dependency(name=name, constraint=constraint, extras=extras)


class ConfigLoader:
    """pyproject.toml oku/yaz işlemlerini yönetir."""

    def __init__(self, project_root: Optional[Path] = None) -> None:
        self.project_root = project_root or find_project_root()
        self.path = self.project_root / "pyproject.toml"

    # ─── Okuma ───────────────────────────────────────────────────────────────

    def load(self) -> ProjectConfig:
        """pyproject.toml'u okur ve ProjectConfig döndürür."""
        if not self.path.is_file():
            raise ConfigError(f"pyproject.toml bulunamadı: {self.path}")

        try:
            doc = tomlkit.loads(self.path.read_text(encoding="utf-8"))
        except tomlkit.exceptions.TOMLKitError as exc:
            raise ConfigError(f"pyproject.toml ayrıştırılamadı: {exc}") from exc

        project_section = doc.get("project", {})
        tool_paketci = doc.get("tool", {}).get("paketci", {})

        deps_raw: list[str] = project_section.get("dependencies", [])
        optional_raw: dict[str, list[str]] = project_section.get("optional-dependencies", {})

        return ProjectConfig(
            name=project_section.get("name", ""),
            version=project_section.get("version", "0.1.0"),
            requires_python=project_section.get("requires-python", ""),
            dependencies=[_parse_dep(d) for d in deps_raw],
            optional_dependencies={
                group: [_parse_dep(d) for d in group_deps]
                for group, group_deps in optional_raw.items()
            },
            lockfile_path=tool_paketci.get("lockfile", "paketci.lock"),
            index_url=tool_paketci.get("index-url", "https://pypi.org/simple"),
            extra_index_urls=list(tool_paketci.get("extra-index-urls", [])),
            trusted_hosts=list(tool_paketci.get("trusted-hosts", [])),
            workspace_members=list(tool_paketci.get("workspace", {}).get("members", [])),
            peer_dependencies=dict(tool_paketci.get("peer-dependencies", {})),
        )

    # ─── Yazma ───────────────────────────────────────────────────────────────

    def add_dependency(self, dep: Dependency, optional_group: Optional[str] = None) -> None:
        """pyproject.toml'a bağımlılık ekler; var olan satırları ve yorumları korur."""
        doc = tomlkit.loads(self.path.read_text(encoding="utf-8"))

        if optional_group:
            target: Container = (
                doc.setdefault("project", tomlkit.table())
                .setdefault("optional-dependencies", tomlkit.table())
                .setdefault(optional_group, tomlkit.array())
            )
        else:
            target = (
                doc.setdefault("project", tomlkit.table())
                .setdefault("dependencies", tomlkit.array())
            )

        pep508 = dep.pep508()
        existing_names = [_parse_dep(str(d)).name.lower() for d in target]
        if dep.name.lower() not in existing_names:
            target.append(pep508)

        self.path.write_text(tomlkit.dumps(doc), encoding="utf-8")

    def remove_dependency(self, name: str, optional_group: Optional[str] = None) -> bool:
        """Bağımlılığı siler. Silindiyse True, bulunamadıysa False döner."""
        doc = tomlkit.loads(self.path.read_text(encoding="utf-8"))

        if optional_group:
            target = (
                doc.get("project", {})
                .get("optional-dependencies", {})
                .get(optional_group, [])
            )
        else:
            target = doc.get("project", {}).get("dependencies", [])

        original_len = len(target)
        to_remove = [d for d in target if _parse_dep(str(d)).name.lower() == name.lower()]
        for item in to_remove:
            target.remove(item)

        if len(target) < original_len:
            self.path.write_text(tomlkit.dumps(doc), encoding="utf-8")
            return True
        return False
