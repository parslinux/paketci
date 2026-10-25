"""TargetEnv birim testleri."""

from __future__ import annotations

from pathlib import Path
import pytest

from paketci.installer.env import TargetEnv


def test_target_env_empty_dir(tmp_path):
    env = TargetEnv(python=Path("/bin/python"), site_packages=tmp_path, scripts_dir=tmp_path / "bin")
    assert env.get_installed_packages() == {}
    assert env.is_installed("requests") is False


def test_target_env_installed_detection(tmp_path):
    # Sahte bir .dist-info oluştur
    dist_info = tmp_path / "my_demo_pkg-1.2.3.dist-info"
    dist_info.mkdir()
    metadata = dist_info / "METADATA"
    metadata.write_text("Metadata-Version: 2.1\nName: My-Demo-Pkg\nVersion: 1.2.3\n")

    env = TargetEnv(python=Path("/bin/python"), site_packages=tmp_path, scripts_dir=tmp_path / "bin")
    pkgs = env.get_installed_packages()
    assert "my-demo-pkg" in pkgs
    assert pkgs["my-demo-pkg"] == "1.2.3"

    assert env.is_installed("my_demo_pkg") is True
    assert env.is_installed("My-Demo-Pkg", "1.2.3") is True
    assert env.is_installed("my-demo-pkg", "2.0.0") is False
    assert env.is_installed("other-pkg") is False
