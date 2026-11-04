# Yayın Kapısı — Respected Brain

Durum: **Windows x64 dondurulmuş paket için doğrulandı**; WSL2/Linux kaynak testleri gerçek, macOS ve Linux dondurulmuş paket doğrulanmadı. Authenticode uygulanmadı.
Bu belge `0.1.0-beta.1` (`0.1.0b1`) yayın paketinin hangi kapılardan geçtiğini ve neyin kapsam dışı olduğunu kaydeder.

## Kapı matrisi

| Kapı | Durum | Kanıt |
|---|---|---|
| Tam birim ve entegrasyon testleri | GEÇTİ | `python -m unittest discover -s tests -t .` → 1073 test OK, 21 skip (Windows 11 x64, 2026-11-04, 426.566 sn, EXIT=0) |
| Şema migration ve eski sürüm fixture'ları | GEÇTİ | `python -m unittest tests.installation.test_migrate -v` → 6 test OK; `STEPS` yalnızca gerçek boşlukları içerir; `tests/fixtures/releases/0.1.0-beta.1/` |
| Dondurulmuş Windows paketi | GEÇTİ | `python packaging/build_dist.py --platform windows --output dist` → `0.1.0b1` |
| Dağıtım bütünlüğü | GEÇTİ | `python -m unittest tests.packaging.test_distribution -v` → 3 test OK |
| Fiziksel kurulum smoke'u | GEÇTİ | `tests/evals/results/br015-native-smoke.json` → 25/25 VERIFIED, `overall=VERIFIED` |
| Hub ortak sözleşme conformance'ı | GEÇTİ | Hub deposunda `python -m unittest discover -s common/conformance -v` → 9 test OK; üç ürünün sözleşme kopyasını denetler |
| Authenticode | UYGULANMADI | Sertifika yok; imzasız paket başarılı imza sayılmaz |
| macOS / Linux / WSL | KISMEN | Windows x64 dondurulmuş paket ve WSL2/Linux kaynak testleri gerçek (BR-019/BR-020); Ubuntu kaynak test job'ı CI matrisinde (BR-026), uzak CI çalıştırılmadı; macOS donanım ve Linux frozen doğrulanmadı |

## Fiziksel smoke kanıtı

Windows 11 x64 üzerinde geçici program, veri, kasa ve HOME köklerinde dondurulmuş paketle şu akış doğrulandı:

1. Temiz kurulum ve dondurulmuş başlatıcı sürümü.
2. Onarım ve iki kez kurucu güncellemesi.
3. Beş istemci için geçici HOME kaydı; proje hook'ları korunuyor.
4. İki aşamalı oturum flush'ı tek günlük kaydında birleşiyor.
5. Güncelleme insan notunu bayt bayt koruyor.
6. Kaldırma yalnızca sahibi olduğu kayıtları geri alıyor; notlar, state, kullanıcı dosyası ve kasa işareti korunuyor.
7. Kaldırma sonrası yeniden kurulum notları/state'i koruyor, kasayı bir kez kaydediyor ve dondurulmuş başlatıcı çalışıyor.

Bu smoke sentetik döküm ve geçici kökler kullanır. Gerçek kullanıcı kasasını, gerçek AI aracı oturumunu veya gerçek sağlayıcı yanıtını kanıtlamaz.

## Yayın kararı

- Windows x64 paketi için test ve veri bütünlüğü kapıları geçti.
- Çok platformlu yayın kapısı geçmedi; doğrulanmamış platformlar desteklenmiş sayılmaz.
- Üretim kod imzalama sertifikası olmadığı için SmartScreen uyarısı beklenir; Authenticode kapısı açık kalır.

## Açık dış bağımlılıklar

BR-029 denetiminde kalan maddeler yeniden kontrol edildi; bunlar kod hatası değil, dış kaynak, donanım veya gerçek üretim kimliği gerektiriyor:

| Madde | Gerçek durum | Neden açık |
|---|---|---|
| Authenticode | `signtool` kurulu değil; kullanıcı deposunda yalnızca `CN=Respected Test Signer` self-signed test sertifikası var | Üretim kod imzalama sertifikası yok; test sertifikası SmartScreen güveni sağlamaz |
| OpenRouter gerçek çağrı | `credential status` → `configured=false`, `source=null` | API anahtarı yok; ücretli çağrı yapılmadı |
| Gemini CLI gerçek oturum | Windows ve WSL2'de `gemini` kurulu değil | Kurulum ve gerçek oturum yapılmadı |
| macOS | Gerçek macOS donanımı yok | Yalnızca platform simülasyonları çalışıyor |
| Linux dondurulmuş paket | Linux frozen artefaktı üretilmedi | WSL2/Linux kaynak testleri gerçek, frozen paket değil |
| Uzak CI | `.github/workflows/ci.yml` içinde job tanımlı | GitHub Actions üzerinde çalıştırılmadı; yerel Linux sonucu CI kanıtı değildir |

## Yeniden üretim

```powershell
python -m unittest discover -s tests -t .
python packaging/build_dist.py --platform windows --output dist
python -m unittest tests.packaging.test_distribution -v
python tests/native/smoke/platform_smoke.py --package dist/RespectedBrain --output tests/evals/results/br015-native-smoke.json
```

Hub ortak conformance'ı, Hub deposunun kökünde `python -m unittest discover -s common/conformance -v` ile çalıştırılır.
