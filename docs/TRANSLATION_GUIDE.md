# paketci Yerelleştirme ve Çoklu Dil Kılavuzu 🌍

Bu kılavuz, `paketci` CLI arayüzünün, yardım metinlerinin ve hata mesajlarının yerelleştirilmesi (i18n / l10n) ile ilgili standartları açıklar.

---

## 1. Dil Politikası

- **Varsayılan CLI Dili:** Türkçe (`tr_TR`) ve evrensel İngilizce (`en_US`).
- **Kod ve Değişken İsimleri:** Standart İngilizce (PEP 8 uyumlu).
- **Kullanıcı Arayüzü (Rich / Typer):** Anlaşılır, samimi ve teknik terimleri yerli yerinde kullanan Türkçe terminal mesajları.

---

## 2. Terminal Mesaj Standartları

Kullanıcı arayüzünde tutarlılık sağlamak amacıyla aşağıdaki görsel standartlar kullanılır:

| Durum | Simge | Stil | Örnek |
|---|---|---|---|
| Başarı | `✔` | `[bold green]` | `✔ Paket başarıyla eklendi.` |
| Bilgi | `ℹ` | `[bold cyan]` | `ℹ 3 paket indiriliyor...` |
| Uyarı | `⚠` | `[bold yellow]` | `⚠ Lockfile eski olabilir.` |
| Hata | `✖` / Panel | `[bold red]` | `Panel("Hata Açıklaması")` |

---

## 3. Yeni Dil Desteği Ekleme

Gelecek sürümlerde gettext veya JSON tabanlı i18n sözlükleri entegre edilecektir:

```json
{
  "tr": {
    "cmd_add_help": "Projeye bağımlılık ekler, çözümler ve kurar.",
    "msg_installed": "Tüm paketler kuruldu."
  },
  "en": {
    "cmd_add_help": "Adds, resolves, and installs dependencies for the project.",
    "msg_installed": "All packages installed."
  }
}
```
Çeviriler `src/paketci/locales/` dizini altında toplanacaktır.
