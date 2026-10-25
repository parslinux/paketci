# paketci — Mimari Dokümantasyonu 🏗️

Bu doküman, `paketci` projesinin katmanlı mimarisini, veri modellerini, domain servislerini ve tasarım prensiplerini detaylandırır.

---

## 1. Tasarım Felsefesi

`paketci`, `pip` gibi geleneksel araçların üzerine kabuk yazmak yerine, Python paketleme ekosisteminin standart, modern yapı taşları üzerine sıfırdan inşa edilmiştir:

- **`resolvelib`:** Pip'in de kullandığı standart SAT benzeri bağımlılık çözümleme motoru.
- **`installer` (PEP 427):** `.whl` dosyalarını doğrudan hedef ortama açan hafif ve hızlı kurulumcu.
- **`tomlkit` (PEP 621):** Yorumları, biçimlendirmeyi ve boşlukları koruyan TOML işleyici.
- **`httpx`:** Asenkron/senkron HTTP ve paralel indirme desteği.
- **`rich` + `typer`:** Modern, renkli ve zengin terminal deneyimi.

---

## 2. Katmanlı Mimari Şeması

Bağımlılıklar kesinlikle tek yönlüdür:

```
┌─────────────────────────────────────────────────────────────┐
│                      CLI Katmanı (typer)                     │
│  init · add · remove · lock · install · sync · update · ... │
└──────────────────────────────┬──────────────────────────────┘
                               │ çağırır
┌──────────────────────────────▼──────────────────────────────┐
│                 core/operations (Orkestrasyon)               │
│  Pipeline: config oku → resolve → lock → fetch → install    │
└──────┬────────┬────────┬────────┬────────┬────────┬─────────┘
       │        │        │        │        │        │
┌──────▼──┐ ┌───▼────┐ ┌─▼──────┐ ┌▼──────┐ ┌▼────┐ ┌▼───────┐
│ config  │ │resolver│ │ index  │ │fetcher│ │inst.│ │lockfile│
└──────┬──┘ └───┬────┘ └─┬──────┘ └┬──────┘ └┬────┘ └┬───────┘
       │        │        │         │         │        │
       └────────┴────────┴────┬────┴─────────┴────────┘
                              │
                    ┌─────────▼────────┐
                    │  utils / logging │
                    └──────────────────┘
```

### Katman Kuralları:
1. **CLI Katmanı İnce Kalır:** Kullanıcı girdilerini doğrular ve `core.operations` fonksiyonunu çağırır. İş mantığı barındırmaz.
2. **`core.operations` Kalındır:** İş akışlarını, servislerin birbirine bağlanmasını ve işlem sırasını yönetir.
3. **Domain Servisleri Birbirini Çağırmaz:** `resolver`, `installer`'ı bilmez; `fetcher`, `config`'i bilmez. Tüm veri alışverişi `core.operations` üzerinden dataclass modelleriyle yapılır.
4. **Hatalar Hiyerarşiktir:** `core.exceptions.PaketciError` temel sınıfından türetilen anlamlı istisnalar fırlatılır.

---

## 3. Domain Servisleri

### 3.1. Config (`src/paketci/config/`)
- `pyproject.toml` standart formatında `[project]` ve `[tool.paketci]` bloklarını okur/yazar.
- `tomlkit` sayesinde kullanıcıların elle yazdığı yorumlar ve format bozulmaz.
- `Dependency` ve `ProjectConfig` modellerini yönetir.

### 3.2. Index (`src/paketci/index/`)
- PyPI JSON API (`https://pypi.org/pypi/<pkg>/json`) istemcisidir.
- `PyPIClient` (sync) ve `AsyncPyPIClient` (async) olarak ikiye ayrılmıştır.
- `MetadataCache`: Disk üzerinde 1 saat TTL ile JSON önbelleği tutar, filelock ile çoklu süreç erişimini korur.

### 3.3. Resolver (`src/paketci/resolver/`)
- **Çift Motorlu Çözümleme Mimarisi:**
  1. `solver.py`: `resolvelib.AbstractProvider` implementasyonu olan `PaketciProvider` sınıfı ve backtracking raporlayıcısı (`PaketciReporter`).
  2. `sat_solver.py`: Saf Python, sıfır dış bağımlılıklı Boolean Satisfiability (SAT / DPLL) motoru. Paket sürümlerini ve çakışan kısıtlamaları CNF (Conjunctive Normal Form) boolean formüllerine dönüştürür; Unit Propagation ve Pure Literal Elimination teknikleriyle deterministik model üretir (`--solver=sat`).
- Çözüm sonucunu `SolveResult` olarak döner.

### 3.4. Lockfile (`src/paketci/lockfile/`)
- Deterministik, sürümlenebilir `paketci.lock` JSON dosyasını yönetir.
- Her paketin tam versiyonu, bağımlılıkları, indirme URL'si ve SHA-256 sağlama toplamını kaydeder.

### 3.5. Fetcher (`src/paketci/fetcher/`)
- `Downloader`: `asyncio.Semaphore` (varsayılan 8 eş zamanlı) ve `httpx.AsyncClient` ile paralel indirme yapar.
- `WheelStore`: İçerik adreslenebilir (`sha256[:2]/<sha256>/<filename>`) global önbellek deposu.
- `hasher.py`: İndirilen her dosyanın SHA-256 hash'ini kilit dosyasıyla doğrular.
- `vcs.py`: Git depolarını (`git+https://...`) sığ klonlama (`--depth 1`) ile yerel önbelleğe çeker ve geliştirici modundaki paketler için sanal ortama doğrudan `.pth` bağlantısı kurar (`add -e`).

### 3.6. Installer (`src/paketci/installer/`)
- `TargetEnv`: Aktif `.venv`, `VIRTUAL_ENV` veya `--target` ortamını tespit eder.
- `wheel.py`: `installer` kütüphanesini kullanarak wheel arşivlerini açar.
- `sdist.py`: Wheel bulunamayan paketleri `build` ile önce wheel'e derler, sonra kurar.
- `idempotent`: Zaten kurulu sürümleri tespit edip indirme ve kurulum adımını atlar.

### 3.7. PEP 517 Build Backend (`src/paketci/build_backend.py`)
- Dış yapı araçlarına (setuptools, flit, hatch vb.) bağımlı olmaksızın projeleri standart `.whl` (Wheel PEP 427) ve `.tar.gz` (sdist) arşivlerine derler.
- `build_wheel` ve `build_sdist` hook'ları tam standart uyumludur.

### 3.8. Güvenlik ve Denetim (`src/paketci/core/audit.py`)
- Projedeki kilitli paketleri OSV.dev (Open Source Vulnerabilities) ve PyPA Advisory veritabanı üzerinden asenkron olarak sorgular.
- CVE ve GHSA zafiyet kimlikleri, etkilenen sürümler ve şiddet (severity) derecelerini tablo halinde sunar.

### 3.9. Global Yapılandırma ve Kimlik Deposu (`src/paketci/config/global_config.py`)
- `~/.config/paketci/config.toml` yolunda kullanıcı/makine düzeyinde ayarları yönetir.
- Hassas token ve parolaları (örn. `auth.token`, `pypi_token`) terminal çıktılarında otomatik maskeler.

### 3.10. Python Araç Zinciri (`src/paketci/core/python_toolchain.py`)
- Sistemdeki tüm Python ikililerini (`python3.10`, `python3.11`, `python3.12`, `python3.13`, `python3.14`) PATH ve standart dizinler üzerinden tarar.
- `.python-version` dosyaları ile proje bazında versiyon sabitleme ve denetimi sağlar.


---

## 4. Ana Operasyon Akışları

### `paketci add <paket>`
1. `config.load()` ile mevcut bağımlılıkları oku.
2. Yeni gereksinimi listeye ekle.
3. `resolver.solve()` ile grafiği PyPI üzerinden çöz.
4. Çözülen grafiği `paketci.lock` dosyasına yaz.
5. `env.is_installed()` ile kurulu olmayan paketleri belirle.
6. `downloader.download_all()` ile eksik paketleri paralel indir.
7. `installer.install_wheel()` ile hedef ortama kur.
8. `config.add_dependency()` ile `pyproject.toml` dosyasını güncelle.

### `paketci install`
1. `paketci.lock` dosyasını oku.
2. Resolver çalıştırılmaz (hız ve determinizm kazancı).
3. Ortamda eksik olan dosyaları önbellekten veya ağdan çek.
4. Hedef ortama kur.
