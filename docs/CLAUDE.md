# CLAUDE.md — Geliştirici ve Model Bağlamı 🤖

Bu dosyanın aslı ve güncel kopyası proje kök dizininde yer almaktadır:
👉 [Kök Dizin CLAUDE.md](../CLAUDE.md)

---

## Özet Bağlam

- **Proje:** `paketci` (Modern, bağımsız Python paket yöneticisi)
- **Mimari:** Tek yönlü katmanlı mimari (`CLI` ➔ `core.operations` ➔ `domain servisleri` ➔ `utils`)
- **Temel Motorlar:** `resolvelib` + `Native SAT (DPLL)` (çözümleme), `installer` (wheel kurulumu), `httpx` (ağ ve indirme), `tomlkit` (pyproject.toml), `paketci.build_backend` (PEP 517).
- **Test Komutu:** `paketci run pytest -v` (73/73 test başarılı)
- **Komut Sayısı:** 25 bağımsız CLI komutu
