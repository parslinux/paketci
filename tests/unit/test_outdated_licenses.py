"""outdated ve licenses operasyonları birim testleri."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from paketci.core import operations
from paketci.lockfile.models import LockedGraph, LockedPackage
from paketci.lockfile import io as lockfile_io


def test_find_outdated_empty_lock(tmp_path):
    (tmp_path / "pyproject.toml").write_text('[project]\nname="demo"\ndependencies=[]\n')
    assert operations.find_outdated(project_root=tmp_path) == []


def test_get_licenses_from_env(tmp_path):
    (tmp_path / "pyproject.toml").write_text('[project]\nname="demo"\ndependencies=[]\n')
    lock_file = tmp_path / "paketci.lock"
    graph = LockedGraph(
        packages={
            "pip": LockedPackage(name="pip", version="24.0"),
        }
    )
    lockfile_io.write(graph, lock_file)

    lics = operations.get_licenses(project_root=tmp_path)
    assert len(lics) == 1
    assert lics[0].name == "pip"
    assert lics[0].version == "24.0"
    assert isinstance(lics[0].license_name, str)
