"""tree, cache ve build birim testleri."""

from __future__ import annotations

from pathlib import Path
import pytest

from paketci.core import operations
from paketci.lockfile.models import LockedFile, LockedGraph, LockedPackage
from paketci.lockfile import io as lockfile_io


def test_dependency_tree(tmp_path):
    (tmp_path / "pyproject.toml").write_text('[project]\nname="demo"\ndependencies=["reqs"]\n')
    lock_file = tmp_path / "paketci.lock"
    graph = LockedGraph(
        packages={
            "reqs": LockedPackage(name="reqs", version="1.0.0", dependencies=["subdep>=0.1"]),
            "subdep": LockedPackage(name="subdep", version="0.2.0"),
        }
    )
    lockfile_io.write(graph, lock_file)

    tree = operations.dependency_tree(project_root=tmp_path)
    assert len(tree) == 1
    assert tree[0].name == "reqs"
    assert tree[0].version == "1.0.0"
    assert len(tree[0].dependencies) == 1
    assert tree[0].dependencies[0].name == "subdep"
    assert tree[0].dependencies[0].version == "0.2.0"


def test_cache_info_and_clean():
    info = operations.cache_info()
    assert isinstance(info.wheel_count, int)
    assert isinstance(info.metadata_count, int)
    assert isinstance(info.total_size_bytes, int)

    deleted_count, freed_bytes = operations.cache_clean()
    assert deleted_count >= 0
    assert freed_bytes >= 0
