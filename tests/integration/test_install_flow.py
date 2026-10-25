"""Integration test — install akışı (mock ile)."""

from __future__ import annotations

import json
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from paketci.lockfile.models import LockedFile, LockedGraph, LockedPackage
from paketci.lockfile import io as lockfile_io


FIXTURE_DIR = Path(__file__).parent.parent / "fixtures"


@pytest.fixture
def project_with_lock(tmp_path):
    """Lockfile'lı örnek proje dizini."""
    pyproject = (FIXTURE_DIR / "pyproject.toml").read_text()
    lockfile_data = (FIXTURE_DIR / "lockfile.json").read_text()
    (tmp_path / "pyproject.toml").write_text(pyproject)
    (tmp_path / "paketci.lock").write_text(lockfile_data)
    return tmp_path


class TestLockfileInstallFlow:
    def test_lockfile_can_be_read(self, project_with_lock):
        lock_path = project_with_lock / "paketci.lock"
        graph = lockfile_io.read(lock_path)
        assert "requests" in graph.packages
        assert graph.packages["requests"].version == "2.32.3"

    def test_list_packages_from_lock(self, project_with_lock):
        from paketci.core import operations
        pkgs = operations.list_packages(project_root=project_with_lock)
        names = [p.name for p in pkgs]
        assert "requests" in names

    def test_why_direct_dependency(self, project_with_lock):
        from paketci.core import operations
        result = operations.why("requests", project_root=project_with_lock)
        assert "<proje>" in result

    def test_why_transitive(self, project_with_lock):
        from paketci.core import operations
        result = operations.why("certifi", project_root=project_with_lock)
        # requests, certifi'yi istiyor
        assert "requests" in result
