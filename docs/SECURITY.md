# paketci Güvenlik Politikası ve Modeli 🛡️

Güvenlik, `paketci` projesinin temel tasarım önceliklerinden biridir. Bu doküman, paketci'nin güvenlik modelini, SHA-256 doğrulamasını ve güvenlik açığı bildirim sürecini açıklar.

---

## 1. Güvenlik Mimarisi ve Koruma Mekanizmaları

### A. Deterministik SHA-256 Hash Doğrulaması
- Çözümleme (`lock`) sırasında her paketin PyPI üzerindeki resmi SHA-256 hash değeri `paketci.lock` içine kaydedilir.
- İndirme (`fetch`) sırasında indirilen her `.whl` veya `.tar.gz` dosyasının sağlama toplamı (`fetcher/hasher.py`) kilit dosyasındaki hash ile bit-seviyesinde karşılaştırılır.
- Hash eşleşmezse dosya anında silinir ve `HashMismatchError` fırlatılır. Bu sayede **Man-in-the-Middle (MitM)** ve bozuk paket saldırıları engellenir.

### B. Supply Chain (Tedarik Zinciri) Koruması
- Paketler asla rastgele URL'lerden veya doğrulanmamış kaynaklardan indirilmez.
- Yalnızca HTTPS üzerinden güvenli TLS bağlantıları kullanılır (`httpx`).
- Kilit dosyası versiyonlanarak (`lockfile_version: 1`) projelerin her makinede bayt-bayt özdeş bağımlılıklarla çalışması garanti edilir.

### C. Yanked (Geri Çekilmiş) Sürüm Koruması
- PyPI üzerinde güvenlik açığı veya kritik hata nedeniyle "yanked" (yayından çekilmiş) olarak işaretlenen sürümler çözümleme motoru tarafından otomatik olarak elenir.

### D. Otomatik Güvenlik Açığı Taraması (`paketci audit`)
- `paketci audit` komutu, kilitli tüm bağımlılıkları OSV.dev (Google Açık Kaynak Güvenlik Veritabanı) ve PyPA Advisory veritabanı üzerinden asenkron olarak sorgular.
- CVE ve GHSA kayıtları, zafiyetin etki derecesi ve yamalanmış sürümleri bildirilir. CI/CD pipeline'larında `--strict` bayrağı ile güvenlik kapısı oluşturulabilir.

### E. Kimlik Bilgisi ve Parola Güvenliği (`paketci config`)
- Global konfigürasyonda (`~/.config/paketci/config.toml`) depolanan API token ve parolalar (`auth.*`) ekrana yazdırılırken (`paketci config list` / `get`) otomatik olarak maskelenir (`sk-***123`).
- Token'ların terminal geçmişine veya ekran görüntülerine sızması önlenir.

### F. Değişmez Kilit Dosyası (`--frozen-lockfile`)
- Üretim veya CI ortamlarında `paketci install --frozen-lockfile` kullanılarak `paketci.lock` dosyasının izinsiz değiştirilmesi engellenir; ortam yalnızca kilitli sürümlerle birebir eşlenir.

---

## 2. Güvenlik Açığı Bildirimi (Reporting Vulnerabilities)

`paketci` projesinde potansiyel bir güvenlik açığı bulursanız, lütfen bunu genel GitHub Issues alanında **paylaşmayın**.

Bunun yerine:
1. `security@paketci.dev` veya proje yöneticisi e-posta adresine detaylı bir e-posta gönderin.
2. Açığın detaylarını, etkilenen sürümleri ve varsa PoC (Proof of Concept) adımlarını ekleyin.
3. Ekibimiz en geç 48 saat içinde geri bildirim sağlayacak ve bir yama (patch) hazırlayacaktır.

Sorumlu bildiriminiz için teşekkür ederiz!
