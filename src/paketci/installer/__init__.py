"""Installer paketi."""

from paketci.installer.env import TargetEnv, detect_env
from paketci.installer.wheel import install_wheel
from paketci.installer.sdist import build_sdist_to_wheel

__all__ = ["TargetEnv", "detect_env", "install_wheel", "build_sdist_to_wheel"]
