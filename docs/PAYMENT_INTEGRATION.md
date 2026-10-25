# Kurumsal Paket ve Ödeme/Lisans Entegrasyonu 💳

Bu doküman, `paketci` altyapısının ücretli, ticari veya lisans korumalı paket ekosistemleriyle (örneğin MCSM Mağaza, kurumsal eklentiler veya özel SaaS kütüphaneleri) nasıl entegre edilebileceğini açıklar.

---

## 1. İş Modeli ve Kullanım Senaryoları

Python ekosisteminde ticari veya lisanslı kütüphaneler genellikle şu modellerle dağıtılır:

1. **Özel Token Korumalı Simple İndeks Deposu:** Kullanıcının satın aldığı lisansa bağlı bir API token veya geçici indirme anahtarı (Signed URL) üretilir.
2. **Paket Düzeyinde Lisans Doğrulama (License Validation):** Kodun çalışma anında veya kurulum anında bir API anahtarı sorgulaması.
3. **MCSM Mağaza / Masaüstü Modülü:** Masaüstü panelinden tek tıkla lisanslı eklenti kurulumu.

---

## 2. Token Tabanlı İndirme Akışı

```
Kullanıcı / MCSM Arayüzü
         │
         ▼ (1. Lisans Satın Al / Token İste)
Ödeme / Mağaza Sunucusu (Payment Gateway: Stripe / Iyzico / vb.)
         │
         ▼ (2. Benzersiz Paketci Token Üret)
Kullanıcı Ortamı (`pyproject.toml`)
         │
         ▼ (3. paketci add ozel-paket --token=xyz)
Özel Depo (Private PyPI Proxy)
         │
         ▼ (4. Token Doğrulandı ➔ Wheel İndir)
Target Environment (.venv)
```

---

## 3. Yapılandırma ve Token Sağlama

Lisanslı paket deposu için token iki şekilde sağlanır:

### Yöntem A: Güvenli Ortam Değişkeni (Önerilen)
```bash
export PAKETCI_EXTRA_INDEX_URL="https://token:${MCSM_LICENSE_KEY}@market.mcsm.io/simple"
paketci install
```

### Yöntem B: `pyproject.toml` ile Statik Tanımlama
```toml
[tool.paketci]
extra-index-urls = [
    "https://token:${LICENSE_KEY}@market.mcsm.io/simple"
]
```

### Yöntem C: `paketci config` ile Kalıcı Token Depolama (CLI Entegre)
```bash
paketci config set auth.market.mcsm.io "MCSM_LICENSE_KEY_XYZ"
paketci install
```

---

## 4. MCSM Mağaza Entegrasyon Kancası (Hook)

MCSM Masaüstü uygulaması üzerinden bir eklenti veya ticari paket satın alındığında:

1. Masaüstü uygulaması arka planda `paketci` CLI'ını çağırır:
   ```bash
   paketci add mcsm-pro-plugin --index-url https://token:LIC_KEY@market.mcsm.io/simple
   ```
2. Kurulum tamamlandığında `paketci check` ile doğrulanır.
3. `paketci licenses` çıktısı ile kullanıcının panelinde eklentinin lisans geçerlilik durumu gösterilir.
