"""Küresel yapılandırma yönetimi (~/.config/paketci/config.toml).

Özel indeksler, API anahtarları, varsayılan ayarlar ve kimlik bilgilerini kalıcı saklar.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import platformdirs
import tomlkit

from paketci.core.exceptions import ConfigError


def get_global_config_path() -> Path:
    """Kullanıcının küresel paketci yapılandırma dosyasının yolunu döndürür."""
    config_dir = platformdirs.user_config_path("paketci")
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "config.toml"


class GlobalConfig:
    """Küresel config.toml okuma ve yazma işlemlerini yönetir."""

    def __init__(self, path: Optional[Path] = None) -> None:
        self.path = path or get_global_config_path()

    def _read_doc(self) -> tomlkit.TOMLDocument:
        if not self.path.is_file():
            return tomlkit.document()
        try:
            return tomlkit.loads(self.path.read_text(encoding="utf-8"))
        except Exception as e:
            raise ConfigError(f"Küresel yapılandırma dosyası okunamadı: {e}") from e

    def _write_doc(self, doc: tomlkit.TOMLDocument) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(tomlkit.dumps(doc), encoding="utf-8")

    def get(self, key: str, default: Any = None) -> Any:
        """Noktalı anahtar ile değer okur (örn: 'index.pypi.token')."""
        doc = self._read_doc()
        parts = key.split(".")
        current = doc
        for p in parts:
            if isinstance(current, dict) and p in current:
                current = current[p]
            else:
                return default
        return current

    def set(self, key: str, value: str) -> None:
        """Noktalı anahtar ile değer yazar (örn: 'index.pypi.token', 'secret')."""
        doc = self._read_doc()
        parts = key.split(".")
        current = doc
        for p in parts[:-1]:
            if p not in current or not isinstance(current[p], dict):
                current[p] = tomlkit.table()
            current = current[p]

        # Otomatik tip dönüşümü (bool / int / str)
        if value.lower() in ("true", "yes", "1"):
            typed_val: Any = True
        elif value.lower() in ("false", "no", "0"):
            typed_val = False
        else:
            try:
                typed_val = int(value)
            except ValueError:
                typed_val = value

        current[parts[-1]] = typed_val
        self._write_doc(doc)

    def unset(self, key: str) -> bool:
        """Belirtilen anahtarı siler."""
        doc = self._read_doc()
        parts = key.split(".")
        current = doc
        for p in parts[:-1]:
            if isinstance(current, dict) and p in current:
                current = current[p]
            else:
                return False

        if isinstance(current, dict) and parts[-1] in current:
            del current[parts[-1]]
            self._write_doc(doc)
            return True
        return False

    def list_all(self) -> Dict[str, Any]:
        """Tüm yapılandırmayı düzleştirilmiş (flat) anahtarlarla döndürür."""
        doc = self._read_doc()
        result: Dict[str, Any] = {}

        def _flatten(d: dict, prefix: str = ""):
            for k, v in d.items():
                full_key = f"{prefix}.{k}" if prefix else k
                if isinstance(v, dict):
                    _flatten(v, full_key)
                else:
                    result[full_key] = v

        _flatten(doc.unwrap())
        return result
