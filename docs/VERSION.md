# paketci Sürüm Numaralandırma Politikası (SemVer) 🏷️

`paketci`, yazılım sürümlerini yönetirken **[SemVer 2.0.0](https://semver.org/) (Semantic Versioning)** ilkelerini benimser.

---

## 1. Sürüm Formatı: `MAJOR.MINOR.PATCH`

Bir sürüm numarası artırılırken şu kurallar uygulanır:

- **MAJOR (Ana Sürüm):** Geriye dönük uyumsuzluk (breaking changes) içeren mimari veya CLI değişikliklerinde artırılır (örn: `1.0.0`).
- **MINOR (Alt Sürüm):** Geriye dönük uyumlu yeni özellikler eklendiğinde artırılır (örn: `0.2.0`).
- **PATCH (Yama Sürümü):** Geriye dönük uyumlu hata düzeltmeleri ve performans iyileştirmelerinde artırılır (örn: `0.1.1`).

---

## 2. Lockfile Sürümleme (`lockfile_version`)

`paketci.lock` JSON dosyasının formatı, CLI sürümünden bağımsız olarak kendi şema sürümünü taşır:

```json
{
  "lockfileVersion": 1,
  "generatedBy": "paketci 0.1.0",
  "python": ">=3.10",
  "packages": { ... }
}
```

- Lockfile şeması değişirse `lockfileVersion: 2` olarak artırılır.
- Eski paketci sürümleri daha yeni bir `lockfileVersion` ile karşılaştığında kullanıcıyı uyarır ve güncellemeyi önerir.

---

## 3. Sürüm Sorgulama ve Yayın Döngüsü

Terminalden anlık sürüm öğrenmek için:
```bash
paketci --version
```

Kod içinden sürüm öğrenmek için:
```python
import paketci
print(paketci.__version__)  # "0.1.0"
```
