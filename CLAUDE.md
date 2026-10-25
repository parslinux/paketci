# paketci — Claude Proje Bağlamı

## Projeyi Bir Cümlede Tanımla

`paketci`, Python paketlerini yöneten modern bir CLI aracıdır. Pip'in üzerine değil, standart kütüphaneler üzerine inşa edilmiştir: `resolvelib` (çözümleme), `installer` (kurulum), `httpx` (ağ), `tomlkit` (config). Hedef: npm/pnpm kalitesinde kullanıcı deneyimi.

---

## Mimari — Tek Yönlü Bağımlılık

```
CLI  -->  core/operations  -->  {config, resolver, index, fetcher, installer, lockfile}  -->  utils
```

- **CLI katmanı ince** — sadece argüman parse eder, `core.operations.*` çağırır.
- **`core/operations.py` kalın** — tüm pipeline orkestrasyon buradadır.
- **Domain servisleri birbirini çağırmaz** — `resolver`, `installer`'ı bilmez.
- **Hata hiyerarşisi `core/exceptions.py`'de** — CLI'de yakalanır.

---

## Dosya Düzeni (Özet)

```
src/paketci/
├── __init__.py          # __version__ = "0.1.0"
├── __main__.py          # python -m paketci
├── cli/
│   ├── app.py           # typer root, --verbose, --version
│   ├── ui.py            # rich console, spinner, tablo
│   └── commands/        # init, add, remove, install, lock, sync, update, list, why, check, run
├── core/
│   ├── operations.py    # TÜM PIPELINE BURAYA GELIR
│   └── exceptions.py    # PaketciError -> ResolveError, FetchError, InstallError...
├── config/
│   ├── models.py        # Dependency, ProjectConfig (dataclass)
│   └── loader.py        # tomlkit ile pyproject.toml oku/yaz (yorum koruyucu)
├── index/
│   ├── client.py        # PyPI JSON API (httpx.AsyncClient)
│   ├── models.py        # PackageMetadata, ReleaseFile
│   └── cache.py         # disk+bellek metadata cache (TTL=1h, filelock)
├── resolver/
│   ├── provider.py      # resolvelib AbstractProvider impl
│   ├── reporter.py      # AbstractReporter (backtracking uyarıları)
│   └── solver.py        # solve() -> SolveResult
├── fetcher/
│   ├── downloader.py    # paralel async indirme (asyncio + semaphore)
│   ├── cache.py         # WheelStore: content-addressable (sha256), hardlink/copy
│   └── hasher.py        # sha256 dogrulama
├── installer/
│   ├── wheel.py         # installer kutuphanesi wrapper
│   ├── sdist.py         # build CLI ile sdist -> wheel
│   └── env.py           # VIRTUAL_ENV / .venv / sistem ortam tespiti
├── lockfile/
│   ├── models.py        # LockedFile, LockedPackage, LockedGraph
│   └── io.py            # JSON lockfile yaz/oku
└── utils/
    ├── paths.py         # platformdirs, link_or_copy, find_project_root
    └── logging.py       # rich RichHandler kurulumu
```

---

## Temel Kararlar — Kod Yazarken Bunlara Uy

### 1. Yeni operasyon = `core/operations.py`'e fonksiyon ekle
CLI'ye iş mantığı koyma. `add_cmd()` sadece argüman alır ve `operations.add(...)` çağırır.

### 2. Hata fırlat, `sys.exit()` değil
Domain katmanında her zaman `PaketciError` alt sınıfı fırlat. CLI'de `except PaketciError` ile yakala, `ui.print_error_panel()` ile göster.

### 3. Async kodunu `asyncio.run()` ile çalıştır
`operations.py` fonksiyonları senkron arayüzdür. Async işleri içeride `asyncio.get_event_loop().run_until_complete()` yerine düzeltilmiş yaklaşımla çalıştır (bkz. progress.md Bilinen Sorunlar #1).

### 4. `tomlkit` kullan, `tomllib` değil
`tomllib` sadece okur ve yorumları yitirir. `tomlkit` hem okur hem yazar, yorumları korur.

### 5. Lockfile formatı (v1 JSON)
```json
{
  "lockfileVersion": 1,
  "generatedBy": "paketci 0.1.0",
  "python": ">=3.11",
  "packages": {
    "<normalize-name>": {
      "version": "x.y.z",
      "files": [{"filename":"...", "url":"...", "sha256":"..."}],
      "dependencies": ["pep508-string", ...]
    }
  }
}
```

### 6. Wheel deposu (content-addressable)
`fetcher/cache.py::WheelStore` — sha256 ile `<store>/<sha256[:2]>/<sha256>/<filename>` yoluna koyar. Aynı wheel farklı projelerde hardlink ile paylaşılır. Hardlink olmayan sistemde `shutil.copy2` fallback'i var.

---

## Aktif Sorunlar (Çözerken Oku)

1. **Resolver async sorunu** (`resolver/provider.py`):
   `find_matches()` ve `get_dependencies()` resolvelib tarafından sync callback olarak çağrılır ama içeriden async PyPI sorgusu yapıyor. Çözüm: `httpx.Client` (sync versiyon) kullan veya resolve öncesi versiyon listelerini toplu ön-fetch et.

2. **`_build_locked_graph()` context dışı** (`core/operations.py`):
   `async with client:` bloğu kapandıktan sonra `_build_locked_graph()` içinde `client` tekrar kullanılıyor. Düzelt: graph inşasını `async with` bloğu içine taşı.

---

## Test Komutları

```bash
# Tüm testler
PYTHONPATH=src .venv/bin/pytest tests/ -v

# Sadece unit
PYTHONPATH=src .venv/bin/pytest tests/unit/ -v

# Belirli test
PYTHONPATH=src .venv/bin/pytest tests/unit/test_config.py -v

# CLI test
PYTHONPATH=src .venv/bin/python -m paketci --help
PYTHONPATH=src .venv/bin/python -m paketci --version
```

---

## Sık Kullanılan Import Şablonları

```python
# Yeni bir operasyon eklemek
from paketci.core.exceptions import PaketciError
from paketci.config.loader import ConfigLoader
from paketci.utils.paths import find_project_root
from paketci.utils.logging import get_logger
logger = get_logger(__name__)

# Yeni bir CLI komutu
import typer
from paketci.cli import ui
from paketci.core import exceptions, operations
app = typer.Typer()
```
