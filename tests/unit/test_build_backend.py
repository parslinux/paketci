"""Unit tests for standalone PEP 517 build backend."""

import tarfile
import zipfile
from paketci import build_backend


def test_build_backend_wheel(tmp_path, monkeypatch):
    proj_dir = tmp_path / "sample_pkg"
    proj_dir.mkdir()
    (proj_dir / "pyproject.toml").write_text(
        """[project]
name = "sample-pkg"
version = "1.2.3"
description = "A sample package"
dependencies = [
    "requests>=2.0",
]

[project.scripts]
sample-cli = "sample_pkg.cli:main"
""",
        encoding="utf-8",
    )
    src_dir = proj_dir / "src" / "sample_pkg"
    src_dir.mkdir(parents=True)
    (src_dir / "__init__.py").write_text('__version__ = "1.2.3"\n')
    (src_dir / "cli.py").write_text("def main(): pass\n")

    monkeypatch.chdir(proj_dir)

    out_dir = tmp_path / "dist"
    out_dir.mkdir()

    wheel_name = build_backend.build_wheel(str(out_dir))
    assert wheel_name == "sample_pkg-1.2.3-py3-none-any.whl"
    wheel_path = out_dir / wheel_name
    assert wheel_path.is_file()

    with zipfile.ZipFile(wheel_path) as zf:
        names = zf.namelist()
        assert "sample_pkg/__init__.py" in names
        assert "sample_pkg/cli.py" in names
        assert "sample_pkg-1.2.3.dist-info/METADATA" in names
        assert "sample_pkg-1.2.3.dist-info/WHEEL" in names
        assert "sample_pkg-1.2.3.dist-info/entry_points.txt" in names
        assert "sample_pkg-1.2.3.dist-info/RECORD" in names

        metadata = zf.read("sample_pkg-1.2.3.dist-info/METADATA").decode()
        assert "Name: sample-pkg" in metadata
        assert "Version: 1.2.3" in metadata
        assert "Requires-Dist: requests>=2.0" in metadata


def test_build_backend_sdist(tmp_path, monkeypatch):
    proj_dir = tmp_path / "sample_pkg"
    proj_dir.mkdir()
    (proj_dir / "pyproject.toml").write_text(
        """[project]
name = "sample-sdist"
version = "0.5.0"
""",
        encoding="utf-8",
    )
    (proj_dir / "README.md").write_text("# Sample Readme\n")

    monkeypatch.chdir(proj_dir)

    out_dir = tmp_path / "dist"
    out_dir.mkdir()

    sdist_name = build_backend.build_sdist(str(out_dir))
    assert sdist_name == "sample-sdist-0.5.0.tar.gz"
    sdist_path = out_dir / sdist_name
    assert sdist_path.is_file()

    with tarfile.open(sdist_path, "r:gz") as tar:
        names = tar.getnames()
        assert "sample-sdist-0.5.0/PKG-INFO" in names
        assert "sample-sdist-0.5.0/pyproject.toml" in names
        assert "sample-sdist-0.5.0/README.md" in names
