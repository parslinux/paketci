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
- **Hata hiyerarşisi `core/exceptions.py`'de** — CLI'de yakalanır.

---

## Dosya Düzeni (Özet)

```
src/paketci/
├── __main__.py          # python -m paketci
├── build_backend.py     # Saf Python PEP 517 build backend (build_wheel, build_sdist)
├── cli/
│   ├── app.py           # typer root, 25 komut, --verbose, --version
│   ├── ui.py            # rich console, spinner, tablo, panel
│   └── commands/        # init, add, remove, install, lock, sync, update, list, why,
│                        # check, run, cache, build, outdated, licenses, publish,
│                        # completion, dedupe, workspace, audit, export, config, python, self-update
├── core/
│   ├── operations.py    # TÜM PIPELINE BURAYA GELIR (25 komut orkestrasyonu)
│   ├── exceptions.py    # PaketciError -> ResolveError, FetchError, InstallError...
│   ├── audit.py         # OSV.dev ve PyPA güvenlik zafiyet tarama motoru
│   ├── export.py        # paketci.lock -> requirements.txt ihracatçısı
│   ├── python_toolchain.py # Sistem Python sürümleri ve .python-version yönetimi
│   └── self_update.py   # GitHub Releases / PyPI canlı güncelleme motoru
├── config/
│   ├── models.py        # Dependency, ProjectConfig (dataclass)
│   ├── loader.py        # tomlkit ile pyproject.toml oku/yaz (yorum koruyucu)
│   └── global_config.py # ~/.config/paketci/config.toml (maskelenmiş auth/token)
├── index/
│   ├── client.py        # PyPI JSON API (httpx.AsyncClient & sync PyPIClient)
│   ├── models.py        # PackageMetadata, ReleaseFile
│   └── cache.py         # disk+bellek metadata cache (TTL=1h, filelock)
├── resolver/
│   ├── provider.py      # resolvelib AbstractProvider impl
│   ├── reporter.py      # AbstractReporter (backtracking uyarıları)
│   ├── solver.py        # solve() -> SolveResult (resolvelib entegrasyonu)
│   └── sat_solver.py    # Saf Python DPLL / SAT bağımlılık çözümleme motoru
├── fetcher/
│   ├── downloader.py    # paralel async indirme (asyncio + semaphore)
│   ├── cache.py         # WheelStore: content-addressable (sha256), hardlink/copy
│   ├── hasher.py        # sha256 dogrulama
│   └── vcs.py           # Git shallow clone ve editable .pth bağlama motoru
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

## Çözülen Kritik Mimari Konular (Resolved)

1. **Resolver async sorunu** (`resolver/provider.py`):
   Sync `PyPIClient` ile `httpx.Client` üzerinden senkron çağrılar ayrılarak event loop çakışmaları tamamen çözüldü.
2. **`_build_locked_graph()` context yönetimi** (`core/operations.py`):
   Client lifecycle context bloğu içine taşınarak çözüldü.
3. **Native SAT (DPLL) Resolver**:
   Pure-Python CNF/DPLL motoru `src/paketci/resolver/sat_solver.py` olarak eklendi ve `--solver=sat` ile çalışır durumda.
4. **Zero-Dependency Build Backend**:
   `src/paketci/build_backend.py` PEP 517 standardına uygun wheel ve sdist üretiyor.
5. **Güvenlik & Audit**:
   OSV.dev ve PyPA veritabanı ile kilitli bağımlılıkları denetleyen `paketci audit` motoru devrede.

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
