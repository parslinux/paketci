"""Config birim testleri."""

from __future__ import annotations

import pytest
from pathlib import Path

from paketci.config.loader import ConfigLoader, _parse_dep
from paketci.config.models import Dependency
from paketci.core.exceptions import ConfigError


SAMPLE_PYPROJECT = """\
[project]
name = "my-app"
version = "1.0.0"
requires-python = ">=3.11"
dependencies = [
    "requests>=2.0",
    "rich[jupyter]>=13",
]

[tool.paketci]
lockfile = "custom.lock"
"""


@pytest.fixture
def project_dir(tmp_path):
    (tmp_path / "pyproject.toml").write_text(SAMPLE_PYPROJECT)
    return tmp_path


class TestParseDep:
    def test_simple(self):
        dep = _parse_dep("requests")
        assert dep.name == "requests"
        assert dep.constraint == ""
        assert dep.extras == []

    def test_with_version(self):
        dep = _parse_dep("requests>=2.0")
        assert dep.name == "requests"
        assert dep.constraint == ">=2.0"

    def test_with_extras(self):
        dep = _parse_dep("rich[jupyter]>=13")
        assert dep.name == "rich"
        assert dep.extras == ["jupyter"]
        assert dep.constraint == ">=13"

    def test_complex_constraint(self):
        dep = _parse_dep("urllib3>=1.21.1,<3")
        assert dep.name == "urllib3"
        assert ">=1.21.1" in dep.constraint


class TestConfigLoader:
    def test_load(self, project_dir):
        loader = ConfigLoader(project_dir)
        config = loader.load()

        assert config.name == "my-app"
        assert config.version == "1.0.0"
        assert config.requires_python == ">=3.11"
        assert len(config.dependencies) == 2
        assert config.lockfile_path == "custom.lock"

    def test_load_missing(self, tmp_path):
        with pytest.raises(ConfigError, match="bulunamadı"):
            ConfigLoader(tmp_path).load()

    def test_add_dependency(self, project_dir):
        loader = ConfigLoader(project_dir)
        loader.add_dependency(Dependency(name="httpx", constraint=">=0.27"))
        config = loader.load()
        names = [d.name for d in config.dependencies]
        assert "httpx" in names

    def test_add_duplicate_skipped(self, project_dir):
        loader = ConfigLoader(project_dir)
        loader.add_dependency(Dependency(name="requests", constraint=">=2.0"))
        config = loader.load()
        req_deps = [d for d in config.dependencies if d.name == "requests"]
        assert len(req_deps) == 1

    def test_remove_dependency(self, project_dir):
        loader = ConfigLoader(project_dir)
        ok = loader.remove_dependency("requests")
        assert ok is True
        config = loader.load()
        names = [d.name for d in config.dependencies]
        assert "requests" not in names

    def test_remove_missing(self, project_dir):
        loader = ConfigLoader(project_dir)
        ok = loader.remove_dependency("nonexistent-pkg")
        assert ok is False
