"""Lockfile birim testleri."""

from __future__ import annotations

import pytest
from pathlib import Path

from paketci.lockfile.models import LockedFile, LockedGraph, LockedPackage
from paketci.lockfile import io as lockfile_io
from paketci.core.exceptions import LockfileError


@pytest.fixture
def sample_graph():
    return LockedGraph(
        lockfile_version=1,
        generated_by="paketci 0.1.0",
        python=">=3.11",
        packages={
            "requests": LockedPackage(
                name="requests",
                version="2.32.3",
                files=[
                    LockedFile(
                        filename="requests-2.32.3-py3-none-any.whl",
                        url="https://files.pythonhosted.org/packages/requests-2.32.3-py3-none-any.whl",
                        sha256="abc123def456",
                    )
                ],
                dependencies=["certifi>=2017.4.17", "urllib3<3,>=1.21.1"],
            )
        },
    )


class TestLockfileRoundtrip:
    def test_write_and_read(self, tmp_path, sample_graph):
        lock_path = tmp_path / "paketci.lock"
        lockfile_io.write(sample_graph, lock_path)

        assert lock_path.is_file()
        loaded = lockfile_io.read(lock_path)

        assert loaded.lockfile_version == 1
        assert "requests" in loaded.packages
        pkg = loaded.packages["requests"]
        assert pkg.version == "2.32.3"
        assert len(pkg.files) == 1
        assert pkg.files[0].sha256 == "abc123def456"
        assert "certifi>=2017.4.17" in pkg.dependencies

    def test_file_not_found(self, tmp_path):
        with pytest.raises(LockfileError, match="bulunamadı"):
            lockfile_io.read(tmp_path / "nonexistent.lock")

    def test_invalid_json(self, tmp_path):
        bad_file = tmp_path / "bad.lock"
        bad_file.write_text("{ not valid json }")
        with pytest.raises(LockfileError, match="ayrıştırılamadı"):
            lockfile_io.read(bad_file)

    def test_version_mismatch(self, tmp_path):
        import json
        data = {"lockfileVersion": 99, "packages": {}}
        bad_file = tmp_path / "bad.lock"
        bad_file.write_text(json.dumps(data))
        with pytest.raises(LockfileError, match="uyumsuz"):
            lockfile_io.read(bad_file)

    def test_empty_graph(self, tmp_path):
        graph = LockedGraph(python=">=3.11")
        lock_path = tmp_path / "empty.lock"
        lockfile_io.write(graph, lock_path)
        loaded = lockfile_io.read(lock_path)
        assert len(loaded.packages) == 0
