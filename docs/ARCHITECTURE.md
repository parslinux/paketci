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
- `resolvelib.AbstractProvider` implementasyonu olan `PaketciProvider` sınıfını barındırır.
- Gelen gereksinimler için geçerli aday sürümleri tarar, backtracking durumlarını `PaketciReporter` ile takip eder.
- Çözüm sonucunu `SolveResult` olarak döner.

### 3.4. Lockfile (`src/paketci/lockfile/`)
- Deterministik, sürümlenebilir `paketci.lock` JSON dosyasını yönetir.
- Her paketin tam versiyonu, bağımlılıkları, indirme URL'si ve SHA-256 sağlama toplamını kaydeder.

### 3.5. Fetcher (`src/paketci/fetcher/`)
- `Downloader`: `asyncio.Semaphore` (varsayılan 8 eş zamanlı) ve `httpx.AsyncClient` ile paralel indirme yapar.
- `WheelStore`: İçerik adreslenebilir (`sha256[:2]/<sha256>/<filename>`) global önbellek deposu.
- `hasher.py`: İndirilen her dosyanın SHA-256 hash'ini kilit dosyasıyla doğrular.

### 3.6. Installer (`src/paketci/installer/`)
- `TargetEnv`: Aktif `.venv`, `VIRTUAL_ENV` veya `--target` ortamını tespit eder.
- `wheel.py`: `installer` kütüphanesini kullanarak wheel arşivlerini açar.
- `sdist.py`: Wheel bulunamayan paketleri `build` ile önce wheel'e derler, sonra kurar.
- `idempotent`: Zaten kurulu sürümleri tespit edip indirme ve kurulum adımını atlar.

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
