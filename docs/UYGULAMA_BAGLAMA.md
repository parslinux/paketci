# Uygulama Bağlama ve MCSM Masaüstü Entegrasyonu 🖥️🔌

Bu kılavuz, `paketci` aracını masaüstü GUI uygulamaları (MCSM Masaüstü, Electron, PySide6, PyQt, Tauri vb.) veya web panelleri içerisinden bir Python kütüphanesi ya da alt süreç (subprocess) olarak çalıştırma rehberidir.

---

## 1. Entegrasyon Yöntemleri

`paketci`, iki farklı yöntemle ana uygulamalara entegre edilebilir:

1. **Python API Olarak (Doğrudan Çağrı):** En performanslı ve saf yöntemdir. Aynı Python süreci içinde çalışır.
2. **CLI Alt Süreci Olarak (`subprocess` / IPC):** Ayrı bir süreçte çalışır; GUI kilitlenmesini önler ve çıktıları anlık JSON/text olarak dinlemenizi sağlar.

---

## 2. Yöntem 1: Python API Olarak Çağırma

`paketci.core.operations` modülü tüm operasyonları temiz birer fonksiyon olarak dışa açar:

```python
from pathlib import Path
from paketci.core import operations

project_dir = Path("/home/user/my-project")

# 1. Proje denetimi
report = operations.check(project_root=project_dir)
if not report.is_healthy:
    print("Eksik paketler:", report.missing_in_env)

# 2. Paket ekleme
operations.add(["requests>=2.31.0", "rich"], project_root=project_dir)

# 3. Kilitli paketleri listeleme
packages = operations.list_packages(project_root=project_dir)
for pkg in packages:
    print(f"Paket: {pkg.name} Sürüm: {pkg.version}")

# 4. Bağımlılık ağacı
tree_nodes = operations.dependency_tree(project_root=project_dir)
```

---

## 3. Yöntem 2: MCSM Masaüstü Subprocess Entegrasyonu

Masaüstü uygulamanız JavaScript/TypeScript (Electron, Tauri) veya bağımsız bir GUI dilindeyse, `paketci` ikilisini arka planda çalıştırıp `stdout` / `stderr` akışını dinleyebilirsiniz:

```javascript
// Electron / Node.js Örneği
const { spawn } = require('child_process');

function runPaketci(args, cwd) {
    return new Promise((resolve, reject) => {
        const proc = spawn('paketci', args, { cwd });

        proc.stdout.on('data', (data) => {
            console.log(`[paketci]: ${data.toString()}`);
            // UI üzerinde progress bar güncelle
        });

        proc.stderr.on('data', (data) => {
            console.error(`[hata]: ${data.toString()}`);
        });

        proc.on('close', (code) => {
            if (code === 0) resolve();
            else reject(new Error(`Exit code: ${code}`));
        });
    });
}

// Kullanım:
await runPaketci(['add', 'requests'], '/path/to/project');
```

---

## 4. UI Durum ve Hata Yönetimi

- `--quiet` bayrağı ile gereksiz loglar gizlenebilir.
- `paketci check` çıkış kodu `0` ise ortam sağlıklıdır; `1` ise eksik paket veya uyumsuzluk vardır.
- `paketci outdated` ile kullanıcıya arayüzde "Güncelleme Mevcut" rozeti gösterilebilir.
- `paketci licenses` ile eklentilerin açık kaynak lisans uyumluluk raporu kullanıcıya sunulabilir.
