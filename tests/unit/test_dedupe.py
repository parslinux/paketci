"""Unit tests for dedupe command and operation."""

from typer.testing import CliRunner

from paketci.cli.app import app
from paketci.core import operations
from paketci.lockfile.models import LockedGraph, LockedPackage

runner = CliRunner()


def test_dedupe_cli_on_current_project():
    result = runner.invoke(app, ["dedupe", "--check"])
    assert result.exit_code == 0
    assert "Bağımlılık Tekilleştirme & Kısıtlama Uyumu" in result.output
    assert "tekilleştirilmiş" in result.output


def test_dedupe_empty_graph(tmp_path):
    # Proje kökü boş olduğunda
    res = operations.dedupe(project_root=tmp_path)
    assert res.packages_checked == 0
    assert res.compatible_count == 0
    assert res.conflict_count == 0


def test_dedupe_with_conflict(tmp_path):
    from paketci.lockfile import io as lockfile_io

    # pyproject.toml oluştur
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """[project]
name = "conflict-test"
version = "0.1.0"
dependencies = [
    "alpha>=2.0",
]
""",
        encoding="utf-8",
    )

    # Lockfile'a alpha==1.0 koy (çakışma durumu)
    graph = LockedGraph(
        packages={
            "alpha": LockedPackage(name="alpha", version="1.0.0", dependencies=[]),
        }
    )
    lockfile_io.write(graph, tmp_path / "paketci.lock")

    res = operations.dedupe(project_root=tmp_path)
    assert res.packages_checked == 1
    assert res.conflict_count == 1
    assert res.compatible_count == 0
    assert not res.reports[0].is_compatible
    assert "alpha" in res.reports[0].package
