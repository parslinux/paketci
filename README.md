# paketci 📦.
> Modern, hızlı ve güvenilir Python paket yöneticisi.

paketci; pip'in üzerine değil, Python ekosisteminin standart araçları üzerine inşa edilmiştir. npm/pnpm kalitesinde bir kullanıcı deneyimi hedefler.

---

## Özellikler

| Özellik | Açıklama |
|---------|----------|
| ⚡ **Paralel İndirme** | `asyncio` + `httpx` ile wheel'ler aynı anda indirilir |
| 🔒 **Deterministik Lockfile** | `resolvelib` tabanlı çözümleme, `paketci.lock` JSON formatı |
| 🗄️ **Content-Addressable Cache** | SHA-256 ile wheel deposu; projeler arası hardlink paylaşımı |
| 🔍 **`why` Komutu** | "Bu paket neden kurulu?" sorusunu ağaç görünümüyle yanıtlar |
| 🌐 **Offline Mod** | `--offline` ile önbellekten kur, ağa çıkma |
| 🧊 **Frozen Lockfile** | `--frozen-lockfile` ile CI'da değişmez kurulum garantisi |
| 🎨 **Zengin CLI** | `typer` + `rich` ile renkli, açıklayıcı terminal çıktısı |

---

## Kurulum

> PyPI'da henüz yayınlanmadı. Kaynaktan kurulum:

```bash
pip install paketci
```

Veya geliştirme ortamı için:

```bash
git clone <repo>
cd paketci
python -m venv .venv && source .venv/bin/activate
pip install -e .
```

---

## Hızlı Başlangıç

```bash
# Yeni bir proje başlat
paketci init my-project

# Bağımlılık ekle
paketci add requests
paketci add "httpx>=0.27" rich

# Lockfile oluştur / güncelle
paketci lock

# Lockfile'dan kur (resolver çalışmaz, hız kazancı)
paketci install

# Ortamı lockfile ile eşitle
paketci sync

# Bağımlılık kaldır
paketci remove requests

# Tüm paketleri listele
paketci list

# "Bu paket neden kurulu?" analizi
paketci why certifi

# Güncelle
paketci update
paketci update httpx
# Proje sağlık kontrolü
paketci check

# Sanal ortamda komut çalıştır
paketci run pytest
paketci run python main.py
```

---

## Komutlar

```
init     Yeni bir Python projesi başlatır (pyproject.toml, README, .gitignore)
add      Projeye bağımlılık ekler, çözümler ve kurar
remove   Projeden bağımlılık kaldırır, lockfile'ı günceller
lock     pyproject.toml'dan deterministik lockfile üretir
install  Lockfile'dan kurar — resolver çalışmaz (idempotent ve paralel)
sync     lock + install (ortamı lockfile ile eşitler)
update   Paket(ler)i en yeni versiyona günceller
list     Kurulu paketleri tablo olarak gösterir
tree     Tüm bağımlılık ağacını hiyerarşik olarak görselleştirir
why      Bir paketin bağımlılık ağacındaki yerini açıklar
check    Proje, lockfile ve sanal ortam sağlık denetimi
run      Proje sanal ortamı bağlamında komut veya betik çalıştırır
cache    Önbellek boyutu görüntüleme (info) ve temizleme (clean)
build    Projeyi PEP 517 standardında wheel ve sdist formatlarına derler
outdated   PyPI'daki daha yeni sürümleri denetler ve listeler
licenses   Projede kullanılan paketlerin lisanslarını listeler
publish    Derlenen paketleri PyPI veya TestPyPI'a yükler
completion Kabuk otomatik tamamlama (bash/zsh/fish) betiğini üretir veya kurar
dedupe     Bağımlılık kısıtlamalarını denetler ve tek sürüm uyumunu doğrular
workspace  Çoklu paket (monorepo) çalışma alanlarını listeler ve komut koşturur
audit      Kilitli paketleri bilinen güvenlik açıklarına (CVE/GHSA) karşı tarar
export     paketci.lock dosyasını standart requirements.txt formatına dönüştürür
config     Küresel yapılandırma ve kimlik bilgisi yönetimi (get/set/list/unset)
python     Sistemdeki Python sürümlerini listeler, hedefler ve sabitler (pin)
self-update paketci paketini doğrudan en son sürüme günceller
```

### Global Seçenekler

```
-v, --verbose          Detaylı çıktı
-q, --quiet            Sadece hataları göster
    --offline          Ağa çıkma, önbellekten kur
    --frozen-lockfile  Lockfile değiştirilmeden kur (CI için)
    --version          Versiyon bilgisi
```

---

## Mimari

```
┌──────────────────────────────────────┐
│           CLI (typer + rich)         │
│  add · remove · lock · install · why │
└──────────────────┬───────────────────┘
                   │
┌──────────────────▼───────────────────┐
│        core/operations.py            │
│   config → resolve → lock →          │
│   fetch → install                    │
└──┬────────┬────────┬────────┬────────┘
   │        │        │        │
config  resolver   fetcher  installer
loader  resolvelib  httpx   installer
        +cache      +cache  lib / build
   │        │        │        │
   └────────┴────────┴────────┘
                   │
              utils (paths, logging)
```

Bağımlılık yönü **tek yönlüdür:**
```
cli → core → {config, resolver, index, fetcher, installer, lockfile} → utils
```

Domain servisleri birbirini **doğrudan çağırmaz**; `core/operations` orkestre eder.

---

## Lockfile Formatı

`paketci.lock` (JSON, v1):

```json
{
  "lockfileVersion": 1,
  "generatedBy": "paketci 0.1.0",
  "python": ">=3.11",
  "packages": {
    "requests": {
      "version": "2.32.3",
      "files": [
        {
          "filename": "requests-2.32.3-py3-none-any.whl",
          "url": "https://...",
          "sha256": "abc123..."
        }
      ],
      "dependencies": ["certifi>=2017.4.17", "urllib3<3,>=1.21.1"]
    }
  }
}
```

---

## Gereksinimler

- Python 3.11+
- İnternet bağlantısı (offline mod hariç)

---

## Kullanılan Kütüphaneler

| Kütüphane | Amaç |
|-----------|------|
| `resolvelib` | Bağımlılık çözümleme motoru |
| `installer` | Wheel kurulumu (PEP 427) |
| `httpx` | Asenkron HTTP istemcisi |
| `tomlkit` | pyproject.toml oku/yaz (yorum koruyucu) |
| `typer` + `rich` | CLI arayüzü |
| `build` | sdist → wheel dönüşümü |
| `platformdirs` | Çapraz platform cache/config dizinleri |
| `filelock` | Önbellek eş zamanlı erişim kilidi |

---

## Geliştirme

```bash
# Testleri çalıştır
PYTHONPATH=src pytest tests/ -v

# CLI'yi test et
PYTHONPATH=src python -m paketci --help
```

---

> 🚀 **MVP Durumu:** `add`, `remove`, `lock`, `install`, `sync`, `update`, `list` ve `why` komutları canlı PyPI çözümleme motoru ve paralel idempotent kurulum altyapısıyla çalışmaktadır.

Geliştirme notları ve ilerleme için [`CLAUDE.md`](CLAUDE.md) ve [`progress.md`](progress.md) dosyalarına bakın.

---

## Lisans
 
Bu proje [MIT Lisansı](LICENSE) altında lisanslanmıştır. Detaylar için [LICENSE](LICENSE) dosyasına bakabilirsiniz.
# paketci
