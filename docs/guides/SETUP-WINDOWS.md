# 🪟 Windows Native Kurulumu

> WSL/Bash gerekmeden çalışan paket kurulumu. Genel akış [SETUP](SETUP.md), yerleşim [mimari](../ARCHITECTURE.md).

## 1. Tam olarak ne nereye kurulur?

```text
%LOCALAPPDATA%/Respected/RespectedBrain/app/
├── respectedbrain.exe
└── app/                         Paket, runtime bağımlılıkları ve resources

%LOCALAPPDATA%/Respected/RespectedBrain/data/
├── config.json
├── install-manifest.json
├── logs/
├── backups/
└── vaults/<UUID>/
    ├── state/
    ├── cache/
    └── overrides/
```

Not kasası bunlardan ayrıdır; örneğin `C:/Users/<kullanıcı>/Documents/BenimBeynim`. Windows Documents yönlendirilmiş olabilir. Native program runtime'ı paketle gelir; DataRoot'a ayrı `runtime/` veya `scripts/` motoru kurulmaz.

## 2. Hub üzerinden kurulum

İki eşdeğer yol vardır; ikisi de ürünün kendi `setup` hizmetini çalıştırır, program, veri ve kasa yolları ayrı tutulur.

- **Hub ile (önerilen):** Hub imzalı native dağıtımı doğrular, kasa yolunu ve AI istemci seçimlerini sorar, `setup` hizmetini çağırır.
- **Bağımsız kurucu:** `RespectedSecondBrain-Windows-Setup.exe` (Inno, kullanıcı başına, admin gerekmez; `packaging/build_installer.py` ile üretilir). Yalnızca kasa klasörünü sorar (sessiz kurulumda `/VAULT="yol"`), dağıtımı geçici klasöre açıp `respectedbrain setup ... --allow-unattested --no-global --no-mcp --no-schedule --no-shortcut` çalıştırır; AI istemci bağlantıları sonradan seçilir. Kurucunun kendi dosyası yalnızca `%LOCALAPPDATA%/Respected/RespectedBrain/installer/unins000.exe` olur; Windows'taki Yüklü uygulamalar girdisini bu kurucu yazar, kaldırma `respectedbrain uninstall --keep-data --allow-unattested` çalıştırır (kasa ve veri klasörü korunur).

Geliştirme sırasında aynı hizmet `respectedbrain setup --vault ... --package ...` ile çağrılabilir.

## 3. Kullanımda executable ve son makbuz

Frozen launcher kendi çalışan dosyasını yerinde değiştirmek/silmek için Windows exit sonrası helper kullanabilir. `pending` sonuç son başarı değildir. Çıktıdaki `tx_id` ile son makbuz yolunu çözün; deferred sonuç DataRoot `backups/deferred-<kimlik>/result.json` altında yazılır. Bazı işlemlerde CLI exit 0 kuyruğa alma başarısını gösterir; receipt/health doğrulaması ayrıca gerekir.

Kurulum sonrasında [ilk çalıştırma](BOOTSTRAP.md), [güncelleme](UPDATE.md), [kaldırma](UNINSTALL.md) rehberlerine geçin. Bilinmeyen dosya/çakışma varsa eski kaldırıcıyı çalıştırarak zorlamayın.
