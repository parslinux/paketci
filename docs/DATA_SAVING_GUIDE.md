# paketci Veri ve Disk Tasarrufu Kılavuzu 💾

`paketci`, özellikle büyük projelerde, CI/CD sunucularında ve kotalı internet bağlantılarında maksimum veri ve disk alanı tasarrufu sağlamak üzere tasarlanmıştır.

---

## 1. Global Content-Addressable WheelStore

Geleneksel paket yöneticileri her sanal ortam veya proje için aynı `.whl` dosyasını tekrar tekrar diske indirir ve yazar. Örneğin 10 farklı projede `torch` veya `pandas` kullanıyorsanız, gigabaytlarca gereksiz disk alanı işgal edilir.

`paketci`, **Content-Addressable Storage (İçerik Adreslenebilir Depolama)** kullanır:

- **Konum:** `~/.cache/paketci/wheel_store/` (Linux/macOS) veya `%LOCALAPPDATA%\paketci\wheel_store\` (Windows).
- **Format:** `<store>/<sha256[:2]>/<sha256>/<dosya_adi.whl>`
- İndirilen her paket, SHA-256 hash'i ile depolanır.

### Hardlink Paylaşımı (POSIX Sistemler):
Linux ve macOS gibi sistemlerde, indirme deposundaki dosya hedef projenin `.venv` ortamına **kopyalanmaz**, doğrudan **hardlink (sabit bağ)** ile bağlanır.
- Diskte ek yer kaplamaz (0 bayt ek yük).
- Kopyalama süresi sıfıra iner (anında kurulum).
- Eğer dosya sistemi sınırları hardlink'e izin vermezse sistem sessizce kopyalama moduna (copy fallback) geçer.

---

## 2. İdempotent Kurulum (Gereksiz İşleri Atlama)

`paketci install` veya `paketci add` çalıştırıldığında:

1. Hedef ortamdaki `site-packages` hızlıca taranır.
2. İstenen sürüm zaten kuruluysa paket atlanır:
   ```
   ✔ requests==2.32.3 zaten kurulu (atlandı)
   ```
3. Ne ağa gereksiz sorgu atılır ne de diske yeniden yazma yapılır.

---

## 3. Offline (Çevrimdışı) Mod

İnternet bağlantınız kısıtlı veya kesik olduğunda:

```bash
paketci install --offline
paketci add requests --offline
```

- `--offline` bayrağı verildiğinde paketci kesinlikle PyPI veya uzak sunuculara HTTP isteği göndermez.
- Yalnızca daha önce indirilmiş ve `WheelStore`'da bulunan paketleri kullanarak kurulumu tamamlar.
- Eğer istenen paket yerel önbellekte bulunmuyorsa açıklayıcı bir `OfflineModeError` verir.

---

## 4. Önbellek Temizliği ve Denetimi

Önbelleğinizin ne kadar yer kapladığını görmek veya temizlemek için:

```bash
# Önbellek boyutunu görüntüle
paketci cache info

# Disk alanını geri kazanmak için önbelleği temizle
paketci cache clean
```
