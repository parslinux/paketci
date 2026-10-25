# paketci Kurulum ve Sistem Gereksinimleri 🛠️

Bu kılavuz, `paketci` aracını sisteminize kurma, sanal ortamları yapılandırma ve farklı işletim sistemlerindeki gereksinimleri açıklar.

---

## 1. Sistem Gereksinimleri

- **Python Sürümü:** Python 3.10 veya daha yenisi (Python 3.11, 3.12, 3.13 ve 3.14 tam uyumludur).
- **İşletim Sistemleri:**
  - Linux (Ubuntu, Debian, Fedora, Arch Linux vb.)
  - macOS (Apple Silicon ve Intel)
  - Windows 10/11 (PowerShell ve CMD)
- **Ağ:** İlk indirmeler için internet bağlantısı; sonrasında offline mod çalışır.

---

## 2. Kurulum Yöntemleri

### A. Geliştirici Modunda (Kaynak Koddan)

Depoyu klonlayıp sanal ortama kurulabilir:

```bash
git clone git@github.com:parslinux/paketci.git
cd paketci

# Sanal ortam oluştur
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Editable olarak kur
pip install -e .
```

Kurulumu doğrulayın:
```bash
paketci --version
paketci --help
```

### B. Tek Başına Bağımsız Kullanım (pipx veya uv tool ile)

Doğrudan izole bir CLI aracı olarak:

```bash
pipx install paketci
# veya
uv tool install paketci
```

### C. Kendi Kendini Güncelleme (Self-Update)

Kurulu olan `paketci` sürümünü doğrudan terminalden yükseltebilirsiniz:

```bash
paketci self-update
paketci self-update --check
```

---

## 3. Sanal Ortam Entegrasyonu

`paketci`, proje dizininde veya sistemde aktif olan sanal ortamı otomatik olarak algılar:

1. Açıkça belirtilmiş `--target <dizin>` bayrağı.
2. `VIRTUAL_ENV` ortam değişkeni (örn. `source .venv/bin/activate` yapılmışsa).
3. Proje kök dizinindeki `.venv` klasörü.
4. Sistem Python ortamı (sanal ortam yoksa).

> 💡 **İpucu:** `paketci run <komut>` kullandığınızda sanal ortamı elle aktif etmenize gerek kalmaz, `paketci` arka planda sanal ortamı otomatik bağlar.

---

## 4. Platform Notları

### Linux / POSIX:
- Dosya hardlink (`link_or_copy`) desteği maksimum performans sağlar; aynı wheel diske yalnızca bir kez yazılır.
- Script yürütülebilir izinleri (`chmod +x`) otomatik ayarlanır.

### Windows:
- Komut dosyaları için `winshell` mekanizması devreye girer.
- Dosya kilitleme ve paralel indirmeler Windows dosya sistemiyle tam uyumludur.
