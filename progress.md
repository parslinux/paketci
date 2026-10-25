# paketci — Geliştirme İlerlemesi

Son güncelleme: 2026-10-22

## Genel Durum: MVP İskeleti Tamamlandi

---

## Tamamlananlar

### Faz 0 — Proje Kurulumu
- [x] `src/` layout, `pyproject.toml`, `.gitignore`
- [x] Sanal ortam (`.venv`) + tum bagimliliklar kuruldu
- [x] Editable install (`pip install -e .`)
- [x] pytest ayari, 27/27 test geciyor

### Faz 1 — Utils ve Temel Altyapi
- [x] `utils/paths.py` — platformdirs, `link_or_copy` (hardlink -> copy fallback)
- [x] `utils/logging.py` — Rich tabanli loglama
- [x] `core/exceptions.py` — Hata hiyerarsisi

### Faz 2 — Config
- [x] `config/models.py` — `Dependency`, `ProjectConfig` dataclass'lari
- [x] `config/loader.py` — tomlkit ile yorum-koruyucu okuma/yazma
  - [x] `load()` — pyproject.toml -> ProjectConfig
  - [x] `add_dependency()` — yinelenen eklemeyi atlar
  - [x] `remove_dependency()` -> bool

### Faz 3 — Index (PyPI)
- [x] `index/models.py` — `PackageMetadata`, `ReleaseFile`
- [x] `index/client.py` — async httpx, `get_metadata()`, `get_versions()`
- [x] `index/cache.py` — bellek + disk (JSON), TTL=1 saat, filelock

### Faz 4 — Resolver
- [x] `resolver/provider.py` — `resolvelib.AbstractProvider` impl
- [x] `resolver/reporter.py` — `AbstractReporter`, backtracking uyarilari
- [x] `resolver/solver.py` — `solve()` orkestrasyon fonksiyonu

### Faz 5 — Lockfile
- [x] `lockfile/models.py` — `LockedFile`, `LockedPackage`, `LockedGraph`
- [x] `lockfile/io.py` — JSON yaz/oku, versiyon kontrolu

### Faz 6 — Fetcher
- [x] `fetcher/hasher.py` — SHA-256 dogrulama
- [x] `fetcher/cache.py` — Content-addressable `WheelStore` (hardlink/copy)
- [x] `fetcher/downloader.py` — paralel async indirme, semaphore, offline mod

### Faz 7 — Installer
- [x] `installer/env.py` — venv/VIRTUAL_ENV/sistem ortam tespiti
- [x] `installer/wheel.py` — `installer` kutuphanesi wrapper
- [x] `installer/sdist.py` — `build` CLI ile sdist -> wheel

### Faz 8 — Core Operations
- [x] `core/operations.py`:
  - [x] `add()` — config oku -> resolve -> lock -> fetch -> install -> config yaz
  - [x] `remove()` — config'den sil -> lockfile guncelle
  - [x] `lock()` — resolve -> lockfile yaz
  - [x] `install()` — lockfile'dan kur (resolver yok)
  - [x] `sync()` — lock + install
  - [x] `update()` — lockfile'i yenile
  - [x] `list_packages()` — lockfile'daki paketler
  - [x] `why()` — bagimlilik agaci analizi

### Faz 9 — CLI
- [x] `cli/ui.py` — Rich console, spinner, tablo, hata paneli
- [x] `cli/commands/` — 8 komut: add, remove, install, lock, sync, update, list, why
- [x] `cli/app.py` — typer root, global --verbose, --quiet, --version

### Faz 10 — Testler
- [x] `tests/unit/test_config.py` (10 test)
- [x] `tests/unit/test_lockfile.py` (5 test)
- [x] `tests/unit/test_resolver.py` (8 test)
- [x] `tests/integration/test_install_flow.py` (4 test)
- [x] `tests/fixtures/pyproject.toml`, `lockfile.json`

---

## Devam Eden / Yarım Kalan

### Resolver — Gercek Akis
- [x] `provider.py`'de `asyncio.get_event_loop()` sorununu coz (Sync PyPIClient ile çözüldü)
- [x] `solver.py` `resolve()` cagrisini duzelt
- [x] PyPI JSON API endpoint düzeltmesi (`https://pypi.org/pypi`)
- [x] `core/__init__.py` circular import temizlendi

### Operations
- [x] `_build_locked_graph()` — sync context altında metadata çekimi düzeltildi
- [x] `add()` — resolve sonrasi tum grafigi kurma ve pyproject.toml guncelleme
- [x] `lock()` — canlı PyPI üzerinde tekil ve çoklu (transitif) paketlerle test edildi
- [x] `list()` ve `why()` — canlı bağımlılık grafiğinde doğrulandı
- [x] `init()` — sıfırdan pyproject.toml, README ve .gitignore başlatma
- [x] `check()` — pyproject.toml, lockfile senkronizasyonu ve sanal ortam sağlık denetimi
- [x] `run_cmd()` — sanal ortam bağlamında komut ve betik çalıştırma

### Fetcher
- [x] Indirme progress bar'i (rich `DownloadColumn`, `TransferSpeedColumn`)
- [x] Toplu paralel indirme batch desteği

### Installer
- [x] Zaten kurulu paket tespiti (idempotent install — `TargetEnv.is_installed`)
- [x] Windows'ta `script_kind` tespiti (`winshell` / `posix`)
- [x] `overwrite_existing=True` ile paket güncelleme çakışmalarının önlenmesi

---

## Sonraki Faz — MVP Calisir Hale Getirme

Oncelik sirasi:

1. [x] **Resolver async sorununu coz** — `paketci lock` gercekten PyPI'dan cozumleme yapsin (Tamamlandı)
2. [x] **Canlı PyPI çözümleme testi** (`six` ve `requests` transitifleri başarıyla kilitlendi)
3. [x] **`paketci list` ve `paketci why` uctan uca test et** (Tamamlandı)
4. [x] **Fetcher indirme progress bar'ı ve indirme optimizasyonu** (Tamamlandı)
5. [x] **Idempotent install** (site-packages'ta zaten bulunan versiyonu tekrar kurmama) (Tamamlandı)
6. [x] **`paketci init`, `paketci check` ve `paketci run` komutları** (Tamamlandı)

---

- [x] `paketci tree` — Hiyerarşik bağımlılık ağacı görselleştirmesi (Tamamlandı)
- [x] `paketci cache info` & `paketci cache clean` — Global önbellek yönetimi (Tamamlandı)
- [x] `paketci build` — PEP 517 izole ortamlarda sdist ve wheel derleme (Tamamlandı)
- [x] `paketci outdated` — PyPI sürüm taraması ve major/minor/patch analizi (Tamamlandı)
- [x] `paketci licenses` — Proje bağımlılıklarının lisanslarını derleme (Tamamlandı)
- [x] `paketci publish` — PyPI / TestPyPI multipart yükleme (Tamamlandı)
- [x] `paketci completion` — Bash/Zsh/Fish/PowerShell otomatik tamamlama (Tamamlandı)
- [x] `paketci dedupe` — Tek sürüm zorlama ve kısıtlama çakışma analizi (Tamamlandı)
- [x] Workspaces / Monorepo desteği (`paketci workspace list/run`) (Tamamlandı)
- [x] GitHub Actions CI iş akışı (`.github/workflows/ci.yml`) (Tamamlandı)
- [x] Peer dependency uyarıları (`[tool.paketci.peer-dependencies]` + plugin heuristics) (Tamamlandı)
- [x] Kendi build backend'i (`paketci.build_backend` PEP 517 standalone) (Tamamlandı)
- [ ] Native SAT solver (opsiyonel Rust/C eklentisi)

---

## Bilinen Sorunlar

| # | Sorun | Dosya | Durum |
|---|-------|-------|-------|
| 1 | `asyncio.get_event_loop()` Python 3.10+ deprecation | `resolver/provider.py` | Çözüldü ✅ |
| 2 | `script_kind` Windows'ta "posix" hardcoded | `installer/wheel.py` | Çözüldü ✅ |
| 3 | `_build_locked_graph()` async context disinda kullaniliyor | `core/operations.py` | Çözüldü ✅ |
| 4 | `core/__init__.py` üzerinden circular import | `core/__init__.py` | Çözüldü ✅ |
| 5 | PyPI JSON API kök URL (`/pypi`) eksikliği | `core/operations.py` | Çözüldü ✅ |

