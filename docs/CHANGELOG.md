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
- **`paketci publish`:** Derlenen paketleri PyPI veya TestPyPI'a güvenli API token ile yükleme (`publish`).
- **`paketci completion`:** Bash, Zsh ve Fish için kabuk otomatik tamamlama betikleri oluşturma ve kurma.
- **`paketci dedupe`:** Bağımlılık kısıtlamalarını denetleme ve tek sürüm uyumunu doğrulama (`dedupe --check`).
- **`paketci workspace`:** Çoklu paket (monorepo) çalışma alanlarını yönetme ve alt paketlerde komut koşturma (`workspace list`, `workspace run`).
- **`paketci audit`:** OSV.dev ve PyPA Advisory veritabanı üzerinden güvenlik açığı (CVE / GHSA) taraması (`audit --strict`).
- **`paketci export`:** `paketci.lock` dosyasını pip uyumlu `requirements.txt` formatına dönüştürme (`export --hashes`).
- **`paketci config`:** Küresel yapılandırma ve kimlik bilgisi yönetimi (`get`, `set`, `list`, `unset`, `path`).
- **`paketci python`:** Sistemdeki Python sürümlerini tarama, listeleme ve `.python-version` ile sabitleme (`pin`, `which`, `list`).
- **`paketci self-update`:** paketci CLI'ını doğrudan GitHub Releases veya PyPI üzerinden tek komutla güncelleme.
- **Native SAT (DPLL) Çözümleme Motoru:** Saf Python Boolean Satisfiability çözücüsü (`--solver=sat`).
- **Saf Python PEP 517 Build Backend:** Sıfır dış bağımlılıkla `build_wheel` ve `build_sdist` hook'ları (`paketci.build_backend`).
- **VCS & Editable Desteği:** `git+https://...` sığ klonlama ve `add -e` ile yerel klasör bağlantıları.

### ⚡ Performans ve İyileştirmeler
- **İdempotent Kurulum:** Kurulu sürümler taranarak gereksiz indirme ve kurulumlar atlanır.
- **Toplu Paralel İndirme:** `asyncio.Semaphore` ve Rich indirme çubuğu ile çoklu dosya indirme desteği.
- **İki Katmanlı Önbellek:** Bellek (Memory) ve disk (JSON) tabanlı metadata önbelleği (TTL=1 saat).
- **Hardlink Wheel Deposu:** Farklı projeler arasında aynı `.whl` dosyaları hardlink ile paylaşılarak disk alanı korunur.
- **Kapsamlı Test Takımı:** 73/73 test (`pytest`) ile %100 başarılı doğrulanmış operasyonlar.

### 🐛 Hata Düzeltmeleri
- Python 3.10+ `asyncio.get_event_loop()` deprecation ve loop çakışmaları sync `PyPIClient` ile giderildi.
- `core/__init__.py` üzerinden oluşan circular import problemi çözüldü.
- PyPI JSON API kök URL endpoint (`/pypi`) eksikliği giderildi.
- Windows sistemlerde script_kind (`winshell` / `posix`) dinamik algılandı.
- Wheel kurulumunda dosya varlığı durumunda oluşan çakışma `overwrite_existing=True` ile çözüldü.
- Fish kabuk tamamlama sözdizimi uyumsuzluğu giderildi.
- Boş bağımlılık grafiğinde dedupe raporlamasının çökmesi engellendi.
- `build_backend` sdist üretiminde varsayılan README ve dosya tarama eksiklikleri giderildi.

