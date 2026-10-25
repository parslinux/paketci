# paketci Projesine Katkı Sağlama Kılavuzu 🤝

`paketci` açık kaynaklı ve topluluk odaklı bir projedir. Katkılarınız için şimdiden teşekkür ederiz!

---

## 1. Geliştirme Ortamını Hazırlama

1. Projeyi çatallayın (Fork) ve yerel makinenize klonlayın:
   ```bash
   git clone https://github.com/<kullanici_adiniz>/paketci.git
   cd paketci
   ```
2. Sanal ortam kurun ve paketci'yi geliştirici bağımlılıklarıyla birlikte editable olarak kurun:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -e ".[dev]" || pip install -e .
   ```

---

## 2. Mimari Kurallara Uyum

Katkı yaparken lütfen projenin [Mimari Prensiplerine](ARCHITECTURE.md) sadık kalın:

- **CLI katmanına iş mantığı yazmayın:** Tüm iş akışları `src/paketci/core/operations.py` içinde yer almalıdır. CLI komutları sadece argümanları alıp `operations` fonksiyonlarını çağırmalıdır.
- **Domain servisleri bağımsız kalmalıdır:** `resolver` modülü asla `installer` veya `fetcher` import etmemelidir.
- **Standart istisnalar:** Hatalar `sys.exit()` ile değil, `core/exceptions.py` altındaki `PaketciError` sınıflarıyla fırlatılmalıdır.
- **`tomlkit` kullanımı:** `pyproject.toml` işlemleri için yalnızca `tomlkit` kullanılmalı, kullanıcı yorumları silinmemelidir.

---

## 3. Test ve Doğrulama

Her yeni özellik veya hata düzeltmesi birim testleriyle desteklenmelidir:

```bash
# Tüm testleri çalıştır (73 test)
paketci run pytest -v

# Sadece birim testleri çalıştır
paketci run pytest tests/unit/ -v

# Kod stili ve lint kontrolü (Ruff)
ruff check .
ruff format --check .

# Pre-commit kancalarını koştur
pre-commit run --all-files
```

---

## 4. Git ve Pull Request (PR) Süreci

1. Yeni bir dal (branch) açın:
   ```bash
   git checkout -b ozellik/yeni-komut-adi
   ```
2. Açıklayıcı commit mesajları kullanın (Conventional Commits önerilir):
   - `feat: paketci tree komutu eklendi`
   - `fix: wheel kurulumunda dosya çakışması giderildi`
   - `docs: CLI_REFERENCE.md güncellendi`
3. Dalınızı uzak depoya itin ve ana depoya karşı Pull Request (PR) açın.
4. PR açıklamasında yapılan değişiklikleri, nedenini ve yapılan testleri özetleyin.
