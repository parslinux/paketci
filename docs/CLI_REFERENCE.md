# paketci CLI Referans Kılavuzu 💻

`paketci`, modern ve anlaşılır bir komut satırı arayüzü sunar. Tüm komutlar, parametreler ve seçenekler aşağıda detaylandırılmıştır.

---

## Genel Kullanım Sözdizimi

```bash
paketci [GLOBAL_OPTIONS] COMMAND [ARGS]...
```

### Global Seçenekler

| Seçenek | Kısa | Açıklama |
|---|---|---|
| `--verbose` | `-v` | Ayrıntılı hata ayıklama (debug) günlüklerini gösterir |
| `--quiet` | `-q` | Sadece kritik hataları gösterir, bilgi mesajlarını gizler |
| `--version` | | Paketci sürüm numarasını ekrana basar ve çıkar |
| `--help` | `-h` | Komut veya genel yardım menüsünü görüntüler |

---

## Komutlar

### 1. `init`
Yeni bir Python projesi başlatır.
```bash
paketci init [PROJE_ADI] [--venv] [--python <SURUM>]
```
- `PROJE_ADI`: Proje adı (varsayılan: bulunulan dizinin adı).
- `--venv`: Otomatik olarak `.venv` sanal ortamı kurar.
- `--python`: Hedef Python sürüm kısıtı (varsayılan: `>=3.10`).

### 2. `add`
Projeye yeni bağımlılık(lar) ekler, çözer, kilitler ve kurar.
```bash
paketci add <paket_adi>... [-e / --editable <YOL>] [--dev] [--group <GRUP>] [--offline]
```
- Örnek: `paketci add requests "httpx>=0.27" rich`
- Git bağımlılığı: `paketci add git+https://github.com/psf/requests.git`
- Geliştirici / Editable mod: `paketci add -e ./yerel-paket` (ortama `.pth` linki bağlar)
- `--dev`: `[project.optional-dependencies.dev]` grubuna ekler.
- `--offline`: Ağa çıkmaz, sadece yerel önbellekteki paketleri kullanır.

### 3. `remove`
Projeden bağımlılığı kaldırır ve lockfile'ı günceller.
```bash
paketci remove <paket_adi>... [--group <GRUP>]
```
- Örnek: `paketci remove requests`

### 4. `lock`
`pyproject.toml` dosyasındaki gereksinimleri çözümleyerek `paketci.lock` oluşturur.
```bash
paketci lock [--solver resolvelib|sat] [--offline]
```
- `--solver`: Çözümleme algoritmasını seçer (`resolvelib` veya `sat`). Varsayılan: `resolvelib`. `sat` seçeneği saf Python DPLL Boolean Satisfiability motorunu kullanır.


### 5. `install`
`paketci.lock` dosyasındaki tüm paketleri kurar. Resolver çalıştırmaz.
```bash
paketci install [--target <DIZIN>] [--offline]
```
- Zaten kurulu paketler otomatik olarak atlanır (idempotent).
- Eksik paketler paralel olarak indirilip kurulur.

### 6. `sync`
Önce `lock` günceller, ardından ortamı lockfile ile eşitler.
```bash
paketci sync [--offline]
```

### 7. `update`
Tüm veya belirli paketlerin en yeni sürümlerini bularak lockfile'ı yeniler.
```bash
paketci update [paket_adi]...
```

### 8. `list`
`paketci.lock` dosyasındaki tüm paketleri ve sürümlerini tablo olarak listeler.
```bash
paketci list
```

### 9. `tree`
Projenin bağımlılık grafiğini hiyerarşik renkli bir ağaç olarak görüntüler.
```bash
paketci tree
```

### 10. `why`
Bir paketin bağımlılık ağacına neden girdiğini gösterir.
```bash
paketci why <paket_adi>
```
- Örnek: `paketci why certifi` ➔ `requests bunu istiyor: certifi>=2017.4.17`

### 11. `check`
`pyproject.toml`, `paketci.lock` ve aktif sanal ortam senkronizasyonunu denetler.
```bash
paketci check
```

### 12. `run`
Proje sanal ortamı (`.venv`) bağlamında komut veya betik çalıştırır.
```bash
paketci run <komut> [argümanlar]...
```
- Örnek: `paketci run pytest tests/`
- Örnek: `paketci run python main.py`

### 13. `cache`
Önbellek istatistiklerini görüntüler veya temizler.
```bash
paketci cache info     # Boyut ve dosya sayısı tablosu
paketci cache clean    # Tüm önbelleği siler
```

### 14. `build`
Projeyi PEP 517 standardında derler.
```bash
paketci build [--sdist/--no-sdist] [--wheel/--no-wheel] [--dest <DIZIN>]
```
- Çıktılar varsayılan olarak `dist/` klasörüne yazılır.

### 15. `outdated`
Kilitli paketlerin PyPI'daki yeni sürümlerini denetler.
```bash
paketci outdated [--pre]
```
- `--pre`: Kararsız ve ön sürüm (alpha/beta/rc) paketleri de dahil eder.

### 16. `licenses`
Projedeki tüm bağımlılıkların lisans türlerini listeler.
```bash
paketci licenses
```

### 17. `publish`
Derlenmiş dağıtım paketlerini (`dist/*.whl`, `dist/*.tar.gz`) PyPI veya TestPyPI'a yükler.
```bash
paketci publish [--dist <DIZIN>] [--repository <URL>] [--token <API_TOKEN>] [--test]
```
- `--test`: `https://test.pypi.org/legacy/` adresine yükler.
- `--token`: PyPI API belirteci (varsayılan: `PYPI_API_TOKEN` ortam değişkeni).

### 18. `completion`
Kabuk otomatik tamamlama (shell completion) betiğini ekrana basar veya doğrudan kurar.
```bash
# Betiği ekrana bas (eval veya dosya yönlendirme için):
paketci completion [bash|zsh|fish|powershell]

# Yapılandırma dosyasına (~/.bashrc, ~/.zshrc) otomatik kur:
paketci completion --install [bash|zsh|fish]
```

### 19. `dedupe`
Kilitli paketlerin gereksinim kısıtlamalarını denetler, çakışmasız tek sürüm (deduplicated) uyumunu doğrular.
```bash
paketci dedupe [--check]
```
- `--check`: Çakışma veya uyumsuzluk durumunda çıkış kodu 1 (exit 1) üretir (CI pipeline'ları için ideal).

### 20. `workspace`
Çoklu paket (monorepo) çalışma alanlarını yönetir.
```bash
# Çalışma alanındaki tüm üye paketleri listele:
paketci workspace list

# Tüm alt paketlerde (veya belirli bir üyede) komut koştur:
paketci workspace run pytest
paketci workspace run --member pkg-a ruff check
```

### 21. `audit`
Projedeki kilitli paketleri bilinen güvenlik açıklarına (CVE ve GHSA) karşı OSV.dev üzerinden tarar.
```bash
paketci audit [--strict]
```
- `--strict`: Zafiyet tespit edildiğinde çıkış kodu 1 (exit 1) üretir (CI güvenlik kapıları için).

### 22. `export`
`paketci.lock` dosyasını pip uyumlu standart `requirements.txt` formatına dönüştürür.
```bash
# Ekrana bas (stdout):
paketci export

# Dosyaya yaz:
paketci export -o requirements.txt

# Hash'siz yalın format:
paketci export -o requirements.txt --no-hashes
```

### 23. `config`
Küresel ayarları ve özel depo kimlik bilgilerini (`~/.config/paketci/config.toml`) yönetir.
```bash
paketci config set index.corp.url https://nexus.corp.local/simple
paketci config set index.corp.token secret-token-xyz
paketci config get index.corp.url
paketci config list
paketci config unset index.corp.token
paketci config path
```

### 24. `python`
Sistemde kurulu Python sürümlerini tarar, hedefler ve projeye sabitler.
```bash
# Sistemdeki Python sürümlerini listele:
paketci python list

# Proje köküne .python-version yazarak sürümü sabitle:
paketci python pin 3.12

# Hedef veya aktif Python executable dosya yolunu göster:
paketci python which
paketci python which 3.11
```

### 25. `self-update`
`paketci` aracını GitHub Releases veya PyPI üzerinden tek komutla günceller.
```bash
# Sadece yeni sürüm kontrolü yap:
paketci self-update --check

# En güncel kararlı sürüme güncelle:
paketci self-update

# Belirli bir sürüme güncelle/indir:
paketci self-update --version 0.1.0
```




