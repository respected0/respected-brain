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

Windows'ta SecondBrain bağımsız bir kurucuyla değil, **Respected Hub** üzerinden kurulur, güncellenir, onarılır ve kaldırılır. Hub imzalı native dağıtımı doğrular, kasa yolunu ve AI istemci seçimlerini sorar, ardından ürünün kendi `setup` hizmetini çalıştırır; program, veri ve kasa yolları ayrı tutulur. Bağımsız Inno kurucusu ve `_inno-*` kabuk komutları kaldırıldı. Geliştirme sırasında aynı hizmet `respectedbrain setup --gui --vault ... --package ...` ile çağrılabilir.

## 3. Kullanımda executable ve son makbuz

Frozen launcher kendi çalışan dosyasını yerinde değiştirmek/silmek için Windows exit sonrası helper kullanabilir. `pending` sonuç son başarı değildir. Çıktıdaki `tx_id` ile son makbuz yolunu çözün; deferred sonuç DataRoot `backups/deferred-<kimlik>/result.json` altında yazılır. Bazı işlemlerde CLI exit 0 kuyruğa alma başarısını gösterir; receipt/health doğrulaması ayrıca gerekir.

Kurulum sonrasında [ilk çalıştırma](BOOTSTRAP.md), [güncelleme](UPDATE.md), [kaldırma](UNINSTALL.md) rehberlerine geçin. Bilinmeyen dosya/çakışma varsa eski kaldırıcıyı çalıştırarak zorlamayın.
