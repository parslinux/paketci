# CLAUDE.md — Geliştirici ve Model Bağlamı 🤖

Bu dosyanın aslı ve güncel kopyası proje kök dizininde yer almaktadır:
👉 [Kök Dizin CLAUDE.md](../CLAUDE.md)

---

## Özet Bağlam

- **Proje:** `paketci` (Modern Python paket yöneticisi)
- **Mimari:** Tek yönlü katmanlı mimari (`CLI` ➔ `core.operations` ➔ `domain servisleri` ➔ `utils`)
- **Temel Motorlar:** `resolvelib` (çözümleme), `installer` (wheel kurulumu), `httpx` (ağ ve indirme), `tomlkit` (pyproject.toml).
- **Test Komutu:** `paketci run pytest -v`
