# 🛠️ Geliştirici Rehberi

> Kaynak geliştirme, dondurulmuş paket üretimi ve canlı kurulum farklı işlemlerdir. Ürün sözleşmesi [SPECIFICATION](../SPECIFICATION.md), modüller [ARCHITECTURE](../ARCHITECTURE.md).

## 1. Ortam

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -e ".[dev]"
.venv\Scripts\python.exe -m respectedbrain --version
```

Python >=3.10; setuptools/wheel/build/PyInstaller `dev` gereksinimleridir. Sürümün tek kaynağı `pyproject.toml`'dur.
Editable kurulum bu checkout'a bağlanır; başka bir klasörden yapılmış eski bir kurulum varsa build aracı dondurmadan
durur, `pip install -e ".[dev]"` ile yeniden kurun.

## 2. Kod okumaya nereden başlarım?

`pyproject.toml → __main__.py → cli.py → bootstrap.py → core/context.py`. Core saf kök/config/bağlam sunar; özellik
modülleri CLI'ı import etmez. Kaynak `src/respectedbrain`, paket tarifleri `packaging`, araçlar `tools`, testler `tests`.

## 3. Dondurulmuş build

```powershell
.venv\Scripts\python.exe tools/build_dist.py --platform windows --output dist
.venv\Scripts\python.exe tools/verify_dist.py --platform windows --distribution dist/RespectedBrain
```

Çıktı `dist/RespectedBrain/` (`respectedbrain.exe`, `app/`, `distribution.json`). Hub bunu imzalı katalog paketine
`respected-hub/release/tools/build_bundle.py secondbrain` ile sarar; `distribution.json` hash'i yayıncı imzası değildir.
`.venv`, `__pycache__`, `build`, `dist`, egg-info üretim dosyalarıdır; `.local/archives` Git dışı yerel kanıttır.

## 4. Doğrulama

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -t .
.venv\Scripts\python.exe tests/native/smoke/platform_smoke.py --package dist/RespectedBrain --output native-smoke.json
git diff --check
```

Test paketi HOME/APPDATA'yı geçici klasöre yönlendirir; testler gerçek kasaya veya AI istemci ayarına dokunamaz.
`dist/` yoksa dağıtım testi atlanır; tam kabul için önce build alın. Düzen ve sınırlar: [TEST-MATRIX](../TEST-MATRIX.md).

## 5. Yayın ve canlı veri

Kaynak push, CI artifact'ı ve release farklıdır. Windows yayın paketleri Hub reposundaki `release/tools` ile üretilip
Hub'ın Ed25519 anahtarıyla imzalanır; CI (`ci.yml`) yalnız Windows'ta build, doğrulama ve testleri çalıştırır. Push
sonrasında sonuç sürekli sorgulanmaz. Kaynak değişikliğini canlı AppData kurulumuna veya kişisel kasaya uygulamayın.
