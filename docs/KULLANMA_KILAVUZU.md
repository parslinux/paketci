# paketci Kullanma Kılavuzu 📖🚀

`paketci`, Python projelerinizi modern, deterministik, ultra hızlı ve güvenli bir şekilde yönetmeniz için tasarlanmış bağımsız bir paket yöneticisidir.

Bu kılavuz; yeni başlayanlardan ileri düzey geliştiricilere kadar adım adım tüm senaryoları, komutları ve en iyi pratikleri içerir.

---

## 📌 İçindekiler
1. [Giriş ve Temel Felsefe](#1-giriş-ve-temel-felsefe)
2. [Kurulum ve Hazırlık](#2-kurulum-ve-hazırlık)
3. [Yeni Bir Proje Başlatma (`init`)](#3-yeni-bir-proje-başlatma-init)
4. [Bağımlılık Yönetimi (`add`, `remove`, `update`)](#4-bağımlılık-yönetimi-add-remove-update)
5. [Deterministik Kurulum ve Kilit Dosyası (`lock`, `install`, `sync`)](#5-deterministik-kurulum-ve-kilit-dosyası-lock-install-sync)
6. [Bağımlılık İnceleme ve Analiz (`list`, `tree`, `why`, `dedupe`)](#6-bağımlılık-inceleme-ve-analiz-list-tree-why-dedupe)
7. [Proje Çalıştırma ve Sağlık Denetimi (`run`, `check`)](#7-proje-çalıştırma-ve-sağlık-denetimi-run-check)
8. [Python Araç Zinciri ve Sürüm Sabitleme (`python`)](#8-python-araç-zinciri-ve-sürüm-sabitleme-python)
9. [Güvenlik ve Zafiyet Taraması (`audit`)](#9-güvenlik-ve-zafiyet-taraması-audit)
10. [Standart Gereksinim Dışa Aktarma (`export`)](#10-standart-gereksinim-dışa-aktarma-export)
11. [Monorepo ve Çoklu Paket Çalışma Alanları (`workspace`)](#11-monorepo-ve-çoklu-paket-çalışma-alanları-workspace)
12. [Paket Derleme ve Yayınlama (`build`, `publish`)](#12-paket-derleme-ve-yayınlama-build-publish)
13. [Global Ayarlar ve Kimlik Bilgisi (`config`)](#13-global-ayarlar-ve-kimlik-bilgisi-config)
14. [Önbellek ve Disk Yönetimi (`cache`)](#14-önbellek-ve-disk-yönetimi-cache)
15. [Kendini Güncelleme (`self-update`)](#15-kendini-güncelleme-self-update)
16. [Sık Sorulan Sorular ve İpuçları (SSS)](#16-sık-sorulan-sorular-ve-ipuçları-sss)

---

## 1. Giriş ve Temel Felsefe

Geleneksel `pip`, her projede aynı paketleri tekrar tekrar indirip diske kopyalayarak hem internetinizi hem de diskinizi tüketir. Ayrıca standart bir kilit dosyası ve SAT tabanlı derinlemesine çakışma çözücüsü sunmaz.

`paketci` şunları sağlar:
* ⚡ **Sıfır Pip Bağımlılığı:** `resolvelib` ve `Native SAT (DPLL)` bağımlılık motoru, doğrudan `installer` ile wheel açma.
* 🗄️ **İçerik Adreslenebilir Depo (Content-Addressable Storage):** İndirilen paketler SHA-256 ile merkezde saklanır; projelerinize **hardlink** ile bağlanarak 0 bayt ek disk alanı harcar.
* 🔒 **Deterministik `paketci.lock`:** Ekibinizdeki veya sunucunuzdaki herkes bit-seviyesinde aynı bağımlılıkları çalıştırır.
* 🛡️ **Dahili Güvenlik Taraması:** OSV.dev ile güvenlik açığı (CVE) denetimi.

---

## 2. Kurulum ve Hazırlık

### Kaynaktan Kurulum:
```bash
git clone git@github.com:parslinux/paketci.git
cd paketci
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### Otomatik Kabuk Tamamlama (Shell Completion)
Komutları ve parametreleri Tab tuşuyla otomatik tamamlamak için kullandığınız kabuğa göre tek seferlik çalıştırın:

```bash
# Bash için:
paketci completion --install bash

# Zsh için:
paketci completion --install zsh

# Fish için:
paketci completion --install fish
```

---

## 3. Yeni Bir Proje Başlatma (`init`)

Yeni bir Python projesi oluştururken `paketci init` size standartlara uygun (`PEP 621`) bir `pyproject.toml`, `.gitignore` ve `README.md` üretir:

```bash
# Bulunduğunuz dizinde başlatmak:
paketci init

# Yeni bir dizin ve sanal ortam ile başlatmak:
paketci init my_app --venv --python ">=3.11"
cd my_app
```

Oluşan `pyproject.toml`:
```toml
[project]
name = "my-app"
version = "0.1.0"
description = "My awesome project"
readme = "README.md"
requires-python = ">=3.11"
dependencies = []
```

---

## 4. Bağımlılık Yönetimi (`add`, `remove`, `update`)

### Paket Ekleme (`add`)
Paket eklediğiniz anda `paketci` bağımlılık grafiğini çözer, `pyproject.toml`'a yazar, `paketci.lock` üretir ve sanal ortama anında kurar:

```bash
# Tekil paket ekleme:
paketci add requests

# Sürüm kısıtı ve birden çok paket ekleme:
paketci add "httpx>=0.27.0" rich typer

# Geliştirme (dev) ortamı bağımlılığı ekleme:
paketci add pytest ruff --dev

# Git deposundan doğrudan paket ekleme:
paketci add git+https://github.com/psf/requests.git

# Yerel paketi geliştirici modunda bağlama (editable / .pth):
paketci add -e ../benim-kutuphanem
```

### Paket Kaldırma (`remove`)
```bash
# Projeden paketi kaldırır ve lockfile'ı temizler:
paketci remove requests
paketci remove pytest --group dev
```

### Paketleri Güncelleme (`update`)
```bash
# Tüm bağımlılıkları izin verilen en yeni sürümlere yükseltir:
paketci update

# Yalnızca belirli bir paketi yükseltir:
paketci update httpx
```

---

## 5. Deterministik Kurulum ve Kilit Dosyası (`lock`, `install`, `sync`)

### `paketci lock`
Projeyi kurmadan sadece bağımlılık grafiğini çözümleyip `paketci.lock` oluşturmak için:
```bash
paketci lock

# Gelişmiş Saf Python DPLL SAT çözücüsünü kullanmak için:
paketci lock --solver=sat
```

### `paketci install`
Mevcut `paketci.lock` dosyasını okuyarak paketleri sanal ortama kurar. **Resolver çalışmaz**, bu sayede kurulum ışık hızında ve tamamen deterministiktir.
```bash
paketci install

# CI/CD ortamında kilit dosyasının asla değişmemesini zorlamak için:
paketci install --frozen-lockfile

# İnternet bağlantısı olmadan yerel önbellekten kurmak için:
paketci install --offline
```

### `paketci sync`
Sanal ortamdaki paketleri tam olarak `paketci.lock` ile eşitler (eksikleri kurar, fazla paketleri temizler):
```bash
paketci sync
```

---

## 6. Bağımlılık İnceleme ve Analiz (`list`, `tree`, `why`, `dedupe`)

### Kurulu Paketleri Listeleme (`list`)
```bash
paketci list
```
*Tüm doğrudan ve dolaylı paketleri, sürümleri ve açıklamalarıyla şık bir Rich tablosunda gösterir.*

### Hiyerarşik Bağımlılık Ağacı (`tree`)
```bash
paketci tree
```
*Hangi paketin hangi alt kütüphaneleri çağırdığını renkli bir ağaç dalı olarak görselleştirir.*

### "Bu Paket Neden Kurulu?" Analizi (`why`)
Büyük projelerde transitif olarak gelen paketlerin geliş sebebini tek komutla bulun:
```bash
paketci why idna
# Çıktı: requests -> urllib3 -> idna
```

### Tek Sürüm Uyum Doğrulaması (`dedupe`)
```bash
paketci dedupe --check
```
*Farklı kütüphanelerin aynı alt paket için çakışan sürüm kısıtları isteyip istemediğini denetler.*

---

## 7. Proje Çalıştırma ve Sağlık Denetimi (`run`, `check`)

### Sanal Ortamı Aktif Etmeden Komut Koşturma (`run`)
`source .venv/bin/activate` yazmanıza gerek yoktur:
```bash
# Projenin sanal ortamında Python veya CLI çalıştırma:
paketci run python main.py
paketci run pytest -v
paketci run ruff check .
```

### Proje Sağlık Denetimi (`check`)
`pyproject.toml`, `paketci.lock` ve kurulu ortam arasındaki tutarlılığı doğrular:
```bash
paketci check
```

---

## 8. Python Araç Zinciri ve Sürüm Sabitleme (`python`)

Sisteminizdeki tüm Python sürümlerini tarayabilir ve projeye sabitleyebilirsiniz:

```bash
# Sistemdeki Python sürümlerini listele:
paketci python list

# Proje köküne .python-version yazarak Python sürümünü sabitle:
paketci python pin 3.12

# Aktif veya aranan Python dosya yolunu öğren:
paketci python which
paketci python which 3.11
```

---

## 9. Güvenlik ve Zafiyet Taraması (`audit`)

`paketci`, OSV.dev (Google Open Source Vulnerabilities) ve PyPA Advisory veritabanı üzerinden projenizdeki CVE / GHSA açıklarını tarar:

```bash
# Güvenlik taraması yap:
paketci audit

# CI/CD pipeline'larında açık varsa derlemeyi durdur (exit 1):
paketci audit --strict
```

---

## 10. Standart Gereksinim Dışa Aktarma (`export`)

`paketci.lock` dosyanızı eski sistemlerle veya Docker imajlarıyla paylaşmak için `requirements.txt` formatına dönüştürebilirsiniz:

```bash
# Ekrana bas:
paketci export

# Dosyaya SHA-256 hash'leri ile yaz (Güvenli format):
paketci export -o requirements.txt

# Hash'siz yalın format:
paketci export -o requirements.txt --no-hashes
```

---

## 11. Monorepo ve Çoklu Paket Çalışma Alanları (`workspace`)

Birden fazla birbiriyle ilişkili paketi tek depoda yönetiyorsanız:

```toml
# pyproject.toml
[tool.paketci.workspace]
members = ["packages/core", "packages/cli", "packages/web"]
```

```bash
# Tüm alt paketleri listele:
paketci workspace list

# Tüm paketlerde sırayla test koştur:
paketci workspace run pytest
```

---

## 12. Paket Derleme ve Yayınlama (`build`, `publish`)

Harici bir `setuptools` veya `wheel` kurmanıza gerek kalmadan, `paketci`'nin yerel PEP 517 motoruyla paketlerinizi derleyip PyPI'a yükleyebilirsiniz:

```bash
# dist/ dizini altına .whl ve .tar.gz üret:
paketci build

# PyPI veya TestPyPI'a yükle:
paketci publish --token pypi-AgEI...
```

---

## 13. Global Ayarlar ve Kimlik Bilgisi (`config`)

Şirket içi özel PyPI adreslerini veya token'ları merkezi olarak yönetin:

```bash
# Özel depo token'ı kaydet (ekranda otomatik maskelenir):
paketci config set auth.nexus.sirket.internal secret_token_xyz

# Varsayılan depoyu değiştir:
paketci config set default_index https://nexus.sirket.internal/simple

# Ayarları listele:
paketci config list

# Ayar sil:
paketci config unset auth.nexus.sirket.internal
```

---

## 14. Önbellek ve Disk Yönetimi (`cache`)

```bash
# Global önbelleğin boyutunu ve depolanan wheel sayısını gör:
paketci cache info

# Önbelleği tamamen temizle:
paketci cache clean
```

---

## 15. Kendini Güncelleme (`self-update`)

Yeni bir sürüm çıktığında `paketci` kendini tek komutla günceller:

```bash
# Yeni sürüm kontrolü yap:
paketci self-update --check

# En yeni sürüme yükselt:
paketci self-update
```

---

## 16. Sık Sorulan Sorular ve İpuçları (SSS)

### S: `paketci add` yaparken internetim yoksa ne yapmalıyım?
> **C:** `--offline` bayrağını kullanın (`paketci add requests --offline`). Paket daha önce başka bir projede indirilmişse WheelStore'dan anında hardlink ile bağlanır.

### S: Sürüm çözümlemesinde karmaşık bir çakışma yaşarsam ne yapmalıyım?
> **C:** `paketci lock --solver=sat` komutunu çalıştırın. Pure-Python DPLL SAT çözücüsü alternatif kombinasyonları tarayarak deterministik çözümü bulacaktır.

### S: Paket lisanslarını nasıl raporlayabilirim?
> **C:** `paketci licenses` komutunu koşturarak projenizdeki tüm lisansları (MIT, Apache, GPL vb.) tablo halinde görebilirsiniz.

---

> 🚀 **ParsLinux & paketci Ekibi:** Sorularınız, önerileriniz veya katkılarınız için [GitHub Depomuza](https://github.com/parslinux/paketci) bekleriz!
