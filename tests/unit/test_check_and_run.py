"""check ve run_cmd operasyonları birim testleri."""

from __future__ import annotations

import sys
from pathlib import Path
import pytest

from paketci.core import operations
from paketci.lockfile.models import LockedGraph, LockedPackage
from paketci.lockfile import io as lockfile_io


def test_check_missing_pyproject(tmp_path):
    report = operations.check(project_root=tmp_path)
    assert report.pyproject_exists is False
    assert report.is_healthy is False


def test_check_missing_lockfile(tmp_path):
    (tmp_path / "pyproject.toml").write_text('[project]\nname="test"\ndependencies=[]\n')
    report = operations.check(project_root=tmp_path)
    assert report.pyproject_exists is True
    assert report.lockfile_exists is False
    assert report.is_healthy is False


def test_check_healthy(tmp_path):
    (tmp_path / "pyproject.toml").write_text('[project]\nname="test"\ndependencies=[]\n')
    lock_file = tmp_path / "paketci.lock"
    lockfile_io.write(LockedGraph(), lock_file)

    report = operations.check(project_root=tmp_path)
    assert report.pyproject_exists is True
    assert report.lockfile_exists is True
    assert report.is_healthy is True


def test_run_cmd_python(tmp_path):
    ret = operations.run_cmd([sys.executable, "-c", "import sys; sys.exit(0)"], project_root=tmp_path)
    assert ret == 0

    ret_fail = operations.run_cmd([sys.executable, "-c", "import sys; sys.exit(42)"], project_root=tmp_path)
    assert ret_fail == 42


def test_check_peer_dependencies(tmp_path):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """[project]
name = "peer-test"
version = "0.1.0"
dependencies = []

[tool.paketci.peer-dependencies]
pytest-asyncio = "pytest>=7.0.0"
""",
        encoding="utf-8",
    )

    # Lockfile contains pytest-asyncio but NOT pytest
    graph = LockedGraph(
        packages={
            "pytest-asyncio": LockedPackage(name="pytest-asyncio", version="0.23.0", dependencies=[]),
        }
    )
    lockfile_io.write(graph, tmp_path / "paketci.lock")

    report = operations.check(project_root=tmp_path)
    assert len(report.peer_warnings) >= 1
    assert any("pytest" in w for w in report.peer_warnings)

