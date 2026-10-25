"""SHA-256 hash doğrulama yardımcıları."""

from __future__ import annotations

import hashlib
from pathlib import Path

from paketci.core.exceptions import FetchError


def sha256_of_file(path: Path) -> str:
    """Bir dosyanın SHA-256 özetini hex string olarak hesaplar."""
    h = hashlib.sha256()
    with open(path, "rb") as fobj:
        for chunk in iter(lambda: fobj.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def verify(path: Path, expected_sha256: str) -> None:
    """
    Dosyanın SHA-256 özetini beklenen değerle karşılaştırır.

    Raises:
        FetchError: Özetler uyuşmuyorsa.
    """
    actual = sha256_of_file(path)
    if actual != expected_sha256:
        raise FetchError(
            f"SHA-256 uyuşmazlığı: {path.name}\n"
            f"  Beklenen : {expected_sha256}\n"
            f"  Hesaplanan: {actual}"
        )
