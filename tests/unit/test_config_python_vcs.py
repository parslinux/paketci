"""Unit tests for GlobalConfig, Python Toolchain, VCS and Self-Update."""

from pathlib import Path
from typer.testing import CliRunner

from paketci.cli.app import app
from paketci.config.global_config import GlobalConfig
from paketci.core import python_toolchain
from paketci.fetcher import vcs

runner = CliRunner()


def test_global_config_crud(tmp_path):
    cfg_file = tmp_path / "config.toml"
    cfg = GlobalConfig(cfg_file)

    # set & get
    cfg.set("indexes.pypi.url", "https://pypi.org/simple")
    cfg.set("indexes.pypi.token", "pypi-token-1234567890")
    cfg.set("defaults.offline", "true")

    assert cfg.get("indexes.pypi.url") == "https://pypi.org/simple"
    assert cfg.get("defaults.offline") is True
    assert cfg.get("nonexistent") is None

    # list_all
    items = cfg.list_all()
    assert items["indexes.pypi.url"] == "https://pypi.org/simple"
    assert items["defaults.offline"] is True

    # unset
    assert cfg.unset("defaults.offline") is True
    assert cfg.get("defaults.offline") is None
    assert cfg.unset("nonexistent") is False


def test_python_toolchain_find():
    pythons = python_toolchain.find_system_pythons()
    assert len(pythons) > 0
    assert any(p.is_active for p in pythons)
    assert all(p.version for p in pythons)


def test_python_pin_and_which(tmp_path):
    pinned = python_toolchain.pin_python_version("3.14", project_root=tmp_path)
    assert pinned.is_file()
    assert python_toolchain.get_pinned_python_version(project_root=tmp_path) == "3.14"


def test_vcs_is_git_url():
    assert vcs.is_git_url("git+https://github.com/psf/requests.git") is True
    assert vcs.is_git_url("https://github.com/psf/requests.git") is True
    assert vcs.is_git_url("requests>=2.0") is False


def test_install_editable(tmp_path):
    # Sahte bir paket dizini
    pkg_dir = tmp_path / "my_local_pkg"
    pkg_dir.mkdir()
    (pkg_dir / "pyproject.toml").write_text('[project]\nname = "my-local-pkg"\nversion = "0.1.0"\n')
    src_dir = pkg_dir / "src" / "my_local_pkg"
    src_dir.mkdir(parents=True)
    (src_dir / "__init__.py").write_text('__version__ = "0.1.0"\n')

    # Mock TargetEnv
    site_packages = tmp_path / "venv" / "lib" / "site-packages"
    site_packages.mkdir(parents=True)

    class MockEnv:
        @property
        def site_packages(self):
            return site_packages

    installed = vcs.install_editable(pkg_dir, MockEnv())
    assert installed == "my-local-pkg"
    assert (site_packages / "__paketci_editable__my-local-pkg.pth").is_file()
    assert (site_packages / "my-local-pkg-0.0.0.dist-info" / "METADATA").is_file()


def test_cli_config_commands(tmp_path, monkeypatch):
    monkeypatch.setattr("paketci.config.global_config.get_global_config_path", lambda: tmp_path / "config.toml")

    res = runner.invoke(app, ["config", "set", "user.name", "Tester"])
    assert res.exit_code == 0
    assert "kaydedildi" in res.output

    res = runner.invoke(app, ["config", "get", "user.name"])
    assert res.exit_code == 0
    assert "Tester" in res.output

    res = runner.invoke(app, ["config", "list"])
    assert res.exit_code == 0
    assert "user.name" in res.output


def test_cli_python_commands(tmp_path, monkeypatch):
    res = runner.invoke(app, ["python", "list"])
    assert res.exit_code == 0
    assert "Sistemde Tespit Edilen Python Sürümleri" in res.output
