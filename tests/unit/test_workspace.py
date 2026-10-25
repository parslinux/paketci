"""Unit tests for workspace finder, operations, and CLI."""

from typer.testing import CliRunner

from paketci.cli.app import app
from paketci.core import operations
from paketci.core.exceptions import ConfigError, PaketciError
from paketci.workspace.finder import find_workspace

runner = CliRunner()


def test_find_workspace_not_defined(tmp_path):
    # Workspace olmayan proje
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('[project]\nname = "simple"\nversion = "0.1.0"\n', encoding="utf-8")
    assert find_workspace(tmp_path) is None


def test_find_workspace_with_members(tmp_path):
    # Kök pyproject.toml
    root_toml = tmp_path / "pyproject.toml"
    root_toml.write_text(
        """[project]
name = "my-monorepo"
version = "0.1.0"

[tool.paketci.workspace]
members = ["packages/*"]
""",
        encoding="utf-8",
    )

    # Alt paket 1
    pkg1_dir = tmp_path / "packages" / "pkg-a"
    pkg1_dir.mkdir(parents=True)
    (pkg1_dir / "pyproject.toml").write_text(
        '[project]\nname = "pkg-a"\nversion = "1.0.0"\ndependencies = ["requests"]\n',
        encoding="utf-8",
    )

    # Alt paket 2
    pkg2_dir = tmp_path / "packages" / "pkg-b"
    pkg2_dir.mkdir(parents=True)
    (pkg2_dir / "pyproject.toml").write_text(
        '[project]\nname = "pkg-b"\nversion = "2.0.0"\n',
        encoding="utf-8",
    )

    ws = find_workspace(tmp_path)
    assert ws is not None
    assert len(ws.members) == 2
    names = {m.name for m in ws.members}
    assert names == {"pkg-a", "pkg-b"}
    assert ws.get_member("pkg-a").version == "1.0.0"
    assert ws.get_member("non-existent") is None


def test_run_workspace_cmd(tmp_path):
    root_toml = tmp_path / "pyproject.toml"
    root_toml.write_text(
        """[project]
name = "runner-mono"
version = "0.1.0"

[tool.paketci.workspace]
members = ["libs/*"]
""",
        encoding="utf-8",
    )

    lib_dir = tmp_path / "libs" / "core-lib"
    lib_dir.mkdir(parents=True)
    (lib_dir / "pyproject.toml").write_text('[project]\nname = "core-lib"\nversion = "0.1.0"\n', encoding="utf-8")

    # Basit bir echo komutu çalıştır
    results = operations.run_workspace_cmd(project_root=tmp_path, command=["python3", "-c", "print('hello')"])
    assert "core-lib" in results
    assert results["core-lib"] == 0
