# paketci Değişiklik Günlüğü (Changelog) 📜

Tüm önemli değişiklikler, yeni özellikler ve hata düzeltmeleri bu dosyada belgelenir.
Proje [Semantic Versioning (SemVer 2.0)](https://semver.org/) prensiplerine uyar.

---

## [0.1.0] - 2026-10-25

### 🚀 Yeni Özellikler
- **Katmanlı Mimari:** CLI, Core, Domain (Config, Index, Resolver, Lockfile, Fetcher, Installer) ve Utils modülleri kuruldu.
- **`paketci init`:** Yeni projeler için PEP 621 `pyproject.toml`, `README.md` ve `.gitignore` oluşturma desteği.
- **`paketci add` & `paketci remove`:** `tomlkit` ile yorum-koruyucu bağımlılık ekleme ve kaldırma.
- **`paketci lock`:** `resolvelib` ve canlı PyPI JSON API entegrasyonuyla deterministik `paketci.lock` üretimi.
- **`paketci install`:** Deterministik lockfile'dan doğrudan hızlı kurulum motoru.
- **`paketci sync`:** Lockfile ve sanal ortam senkronizasyonu.
- **`paketci update`:** Kilitli paketleri en yeni uyumlu sürümlere yükseltme.
- **`paketci list` & `paketci why`:** Kilitli paketleri listeleme ve bağımlılık gerekçesi ağaç analizi.
- **`paketci tree`:** Renkli Rich Tree hiyerarşik bağımlılık grafiği.
- **`paketci check`:** Lockfile ve sanal ortam sağlık denetimi.
- **`paketci run`:** `.venv` bağlamında betik ve komut çalıştırma.
- **`paketci cache [info|clean]`:** Content-addressable önbellek depolama yönetimi.
- **`paketci build`:** PEP 517 standardında izole sdist ve wheel derleme.
- **`paketci outdated`:** PyPI üzerindeki major/minor/patch yeni sürümleri denetleme.
- **`paketci licenses`:** Sanal ortamdaki paket lisanslarını tarama ve listeleme.

### ⚡ Performans ve İyileştirmeler
- **İdempotent Kurulum:** Kurulu sürümler taranarak gereksiz indirme ve kurulumlar atlanır.
- **Toplu Paralel İndirme:** `asyncio.Semaphore` ve Rich indirme çubuğu ile çoklu dosya indirme desteği.
- **İki Katmanlı Önbellek:** Bellek (Memory) ve disk (JSON) tabanlı metadata önbelleği (TTL=1 saat).
- **Hardlink Wheel Deposu:** Farklı projeler arasında aynı `.whl` dosyaları hardlink ile paylaşılarak disk alanı korunur.

### 🐛 Hata Düzeltmeleri
- Python 3.10+ `asyncio.get_event_loop()` deprecation ve loop çakışmaları sync `PyPIClient` ile giderildi.
- `core/__init__.py` üzerinden oluşan circular import problemi çözüldü.
- PyPI JSON API kök URL endpoint (`/pypi`) eksikliği giderildi.
- Windows sistemlerde script_kind (`winshell` / `posix`) dinamik algılandı.
- Wheel kurulumunda dosya varlığı durumunda oluşan çakışma `overwrite_existing=True` ile çözüldü.
