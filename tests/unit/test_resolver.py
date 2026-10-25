"""Resolver birim testleri."""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from paketci.resolver.provider import PaketciProvider, _normalize
from paketci.index.models import PackageMetadata, ReleaseFile
from paketci.index.cache import MetadataCache
from paketci.index.client import PyPIClient


class TestNormalize:
    def test_dashes_to_dashes(self):
        assert _normalize("my-package") == "my-package"

    def test_underscores_to_dashes(self):
        assert _normalize("my_package") == "my-package"

    def test_dots_to_dashes(self):
        assert _normalize("my.package") == "my-package"

    def test_uppercase(self):
        assert _normalize("MyPackage") == "mypackage"


class TestMetadataCache:
    def test_set_and_get(self, tmp_path):
        cache = MetadataCache(cache_dir=tmp_path, ttl=3600)
        meta = PackageMetadata(
            name="requests",
            version="2.32.3",
            requires_python=">=3.7",
            requires_dist=["certifi>=2017.4.17"],
            files=[],
        )
        cache.set(meta)
        result = cache.get("requests", "2.32.3")
        assert result is not None
        assert result.name == "requests"
        assert result.version == "2.32.3"

    def test_miss(self, tmp_path):
        cache = MetadataCache(cache_dir=tmp_path)
        assert cache.get("nonexistent", "1.0.0") is None

    def test_ttl_expired(self, tmp_path):
        import time, json
        cache = MetadataCache(cache_dir=tmp_path, ttl=1)
        meta = PackageMetadata(name="pkg", version="1.0", files=[])
        cache.set(meta)

        # TTL'yi geç
        key = "pkg_1.0"
        path = tmp_path / f"{key}.json"
        data = json.loads(path.read_text())
        data["_ts"] = time.time() - 10  # 10 saniye öncesi
        path.write_text(json.dumps(data))
        cache._memory.clear()  # bellek cache'ini temizle

        assert cache.get("pkg", "1.0") is None

    def test_invalidate(self, tmp_path):
        cache = MetadataCache(cache_dir=tmp_path)
        meta = PackageMetadata(name="pkg", version="2.0", files=[])
        cache.set(meta)
        cache.invalidate("pkg", "2.0")
        assert cache.get("pkg", "2.0") is None


class TestSolveWithMock:
    def test_solve_simple_dependency(self, tmp_path):
        from paketci.resolver.solver import solve

        mock_client = MagicMock()
        mock_client.get_versions.side_effect = lambda name: {
            "requests": ["2.32.3", "2.31.0"],
            "certifi": ["2024.2.2"],
        }.get(name, [])

        def fake_metadata(name, version=None):
            if name == "requests":
                return PackageMetadata(
                    name="requests",
                    version="2.32.3",
                    requires_dist=["certifi>=2024.0.0"],
                    files=[],
                )
            elif name == "certifi":
                return PackageMetadata(
                    name="certifi",
                    version="2024.2.2",
                    requires_dist=[],
                    files=[],
                )
            raise ValueError(f"Unknown {name}")

        mock_client.get_metadata.side_effect = fake_metadata
        cache = MetadataCache(cache_dir=tmp_path)

        result = solve(["requests>=2.32.0"], mock_client, cache)
        resolved = dict(result.resolved_packages())

        assert "requests" in resolved
        assert resolved["requests"] == "2.32.3"
        assert "certifi" in resolved
        assert resolved["certifi"] == "2024.2.2"

    def test_solve_incompatible_dependency_raises(self, tmp_path):
        from paketci.resolver.solver import solve
        from paketci.core.exceptions import ResolveError

        mock_client = MagicMock()
        mock_client.get_versions.return_value = ["1.0.0"]
        mock_client.get_metadata.return_value = PackageMetadata(
            name="demo", version="1.0.0", files=[]
        )
        cache = MetadataCache(cache_dir=tmp_path)

        with pytest.raises(ResolveError):
            solve(["demo>2.0.0"], mock_client, cache)

