"""init operasyonu birim testleri."""

from __future__ import annotations

from pathlib import Path
import pytest

from paketci.core import operations
from paketci.core.exceptions import ConfigError


def test_init_creates_files(tmp_path):
    pyproject = operations.init(name="harika-proje", directory=tmp_path, requires_python=">=3.11")
    assert pyproject.is_file()
    assert (tmp_path / "README.md").is_file()
    assert (tmp_path / ".gitignore").is_file()

    content = pyproject.read_text()
    assert 'name = "harika-proje"' in content
    assert 'requires-python = ">=3.11"' in content
    assert '[tool.paketci]' in content


def test_init_existing_raises(tmp_path):
    operations.init(directory=tmp_path)
    with pytest.raises(ConfigError):
        operations.init(directory=tmp_path)
