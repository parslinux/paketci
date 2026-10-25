# Flatpak ve Linux Masaüstü Paketleme Kılavuzu 📦🐧

Bu kılavuz, `paketci` aracını veya `paketci` ile yönetilen Python projelerini Flatpak sandbox (yalıtılmış) ortamlarında paketleme ve dağıtma sürecini ele alır.

---

## 1. Flatpak'ta Python Paketleme Zorlukları

Flatpak uygulamaları build aşamasında varsayılan olarak internet erişimine sahip değildir (offline build zorunluluğu). Geleneksel `pip install` komutları ağ erişimi istediği için build sürecinde başarısız olur.

`paketci`, bu sorunu çözmek için ideal bir yapı sunar:

- **Deterministik `paketci.lock`:** Paketlerin tam indirme URL'leri ve SHA-256 hash'leri bellidir.
- **`--offline` ve `--target` Desteği:** İndirilmiş wheel arşivlerini internet bağlantısı olmadan doğrudan `/app/lib/pythonX.Y/site-packages` içine kurabilir.

---

## 2. Flatpak Manifest Entegrasyonu

Flatpak manifest dosyanızda (`org.example.App.yaml` veya `.json`) bağımlılıkları tanımlarken `paketci.lock` içeriğinden yararlanabilirsiniz.

### Örnek Manifest Modülü (YAML):

```yaml
modules:
  - name: python-dependencies
    buildsystem: simple
    build-commands:
      # Önceden indirilmiş wheel arşivlerini /app dizinine kur
      - paketci install --target=/app/lib/python3.11/site-packages --offline
    sources:
      # paketci.lock içindeki dosyalar buraya source olarak listelenir
      - type: file
        url: https://files.pythonhosted.org/packages/.../requests-2.32.3-py3-none-any.whl
        sha256: 70761ce030e8b394e7d9d238386e2b25e4764c1b8a023f4f668f17767146ac43
      - type: file
        url: https://files.pythonhosted.org/packages/.../urllib3-2.2.2-py3-none-any.whl
        sha256: a44f73d1f850550c609c065f4ec1394f71a980ca02ff227eb0fb3b08e705b637
```

---

## 3. Flatpak Sandbox İçinde paketci Çalıştırma

Eğer Flatpak içinde kullanıcıya paket yönetimi yaptıracaksanız:

1. **Önbellek İzinleri:**
   Flatpak manifestinde `~/.cache/paketci` dizini için okuma/yazma izni verilmelidir:
   ```yaml
   finish-args:
     - --filesystem=xdg-cache/paketci:create
   ```
2. **Kullanıcı Kurulumları (`--target`):**
   Flatpak sistemi salt-okunur (`/app`) olduğundan, çalışma anında kurulan paketler kullanıcı dizinine yönlendirilmelidir:
   ```bash
   paketci install --target=~/.var/app/org.example.App/data/python/site-packages
   ```
