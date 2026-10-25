# paketci Test Stratejisi ve Rehberi 🧪

`paketci`, yüksek güvenilirlik ve determinizm sağlamak için kapsamlı bir birim (unit) ve entegrasyon (integration) test takımına sahiptir.

---

## 1. Test Takımını Çalıştırma

Tüm testler `pytest` ile koşturulur:

```bash
# Sanal ortam bağlamında tüm testleri çalıştır
paketci run pytest -v

# Kısa özet ile çalıştır
paketci run pytest -q

# Yalnızca birim testleri koştur
paketci run pytest tests/unit/ -v

# Belirli bir test dosyasını çalıştır
paketci run pytest tests/unit/test_config.py -v
```

---

## 2. Test Dizini Düzeni

```
tests/
├── unit/
│   ├── test_config.py           # pyproject.toml okuma, yazma, parse testleri
│   ├── test_lockfile.py         # paketci.lock JSON serialize/deserialize
│   ├── test_resolver.py         # Çözümleme algoritması ve mock PyPI testleri
│   ├── test_env.py              # Sanal ortam algılama ve kurulu paket tespiti
│   ├── test_init.py             # paketci init komut testleri
│   ├── test_check_and_run.py    # paketci check ve paketci run testleri
│   ├── test_tree_cache_build.py # tree, cache ve build operasyon testleri
│   └── test_outdated_licenses.py# outdated ve licenses operasyon testleri
├── integration/
│   └── test_install_flow.py     # Uçtan uca kurulum, okuma ve listeleme testleri
└── fixtures/                    # Test örnek verileri ve mock dosyaları
```

---

## 3. Test Tasarım İlkeleri

1. **Ağ Bağımsızlığı (Mocking):** Birim testleri gerçek internet erişimine bağımlı olmamalıdır (`unittest.mock.MagicMock` veya fixture'lar ile PyPI yanıtları taklit edilir).
2. **Geçici Dizin İzolasyonu:** Dosya sistemi testlerinde `pytest`'in sağladığı `tmp_path` fixture'ı kullanılarak her test izole bir sandbox içinde çalıştırılır.
3. **Hızlı Çalışma:** 40+ testin tamamı standart bir makinede **0.3 saniyenin altında** tamamlanmalıdır.
