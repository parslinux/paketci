# Özel ve Self-Hosted PyPI Deposu Kullanım Kılavuzu 🏢

Şirket içi kapalı ağlarda veya özel paketlerinizi barındırdığınız depolarda `paketci` kullanımını bu rehberden takip edebilirsiniz.

---

## 1. Desteklenen Özel Depo Çözümleri

`paketci`, PEP 503 (Simple Repository API) ve standart PyPI JSON API ile uyumlu tüm depoları destekler:

- **devpi** (Gelişmiş yerel PyPI proxy ve önbellek)
- **Sonatype Nexus Repository** (Kurumsal paket deposu)
- **JFrog Artifactory**
- **pypiserver** (Minimalist yerel sunucu)
- **AWS CodeArtifact / Google Artifact Registry / Azure Artifacts**

---

## 2. Yapılandırma (`pyproject.toml`)

Projenizin `pyproject.toml` dosyası içinde `[tool.paketci]` bölümünü düzenleyerek varsayılan veya ek depo adreslerini tanımlayabilirsiniz:

```toml
[tool.paketci]
lockfile-path = "paketci.lock"

# Ana indeks deposu (PyPI yerine şirket içi depo)
index-url = "https://pypi.sirketiniz.internal/simple"

# Ek indeks depoları (önce buraya, sonra ana depoya bakar)
extra-index-urls = [
    "https://ozel-paketler.sirketiniz.internal/simple"
]

# SSL sertifikası olmayan veya özel CA kullanan yerel hostlar
trusted-hosts = [
    "pypi.sirketiniz.internal",
    "ozel-paketler.sirketiniz.internal"
]
```

---

## 3. Kimlik Doğrulama (Authentication)

Özel depolara erişirken şifre veya API Token kullanmak için URL içine gömme veya ortam değişkeni yöntemi tercih edilir:

### A. URL İçinde Token Kullanımı:
```toml
index-url = "https://__token__:pypi-AgEIcHlwaS5vcmc.../simple"
```

### B. Ortam Değişkeni Kullanımı:
`paketci`, standart `PIP_INDEX_URL` ve `PAKETCI_INDEX_URL` ortam değişkenlerini otomatik olarak tanır:

```bash
export PAKETCI_INDEX_URL="https://kullanici:parola@pypi.sirket.com/simple"
paketci install
```

---

## 4. Yerel devpi / pypiserver Hızlı Kurulumu

Geliştirme amacıyla yerel bir proxy deposu ayağa kaldırmak için:

```bash
# pypiserver ile yerel depo
pip install pypiserver
pypiserver run -p 8080 ~/packages

# paketci ile kullan
paketci add mypkg --index-url http://localhost:8080/simple
```
