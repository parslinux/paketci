"""Hata hiyerarşisi — tüm paketci hataları buradan türer."""

from __future__ import annotations


class PaketciError(Exception):
    """Tüm paketci hatalarının temel sınıfı."""


class ConfigError(PaketciError):
    """pyproject.toml okuma/yazma hataları."""


class ResolveError(PaketciError):
    """Bağımlılık çözümleme hataları (çakışma vb.)."""


class FetchError(PaketciError):
    """Ağ veya hash doğrulama hataları."""


class InstallError(PaketciError):
    """Wheel kurulum hataları."""


class LockfileError(PaketciError):
    """Lockfile okuma/yazma hataları."""


class OfflineModeError(FetchError):
    """Offline modda ağ erişimi gerektiren işlem denendi."""


class FrozenLockfileError(PaketciError):
    """--frozen-lockfile aktifken lockfile değişikliği tespit edildi."""


class EnvironmentError(PaketciError):  # noqa: A001
    """Hedef ortam (venv/site-packages) tespit hatası."""
