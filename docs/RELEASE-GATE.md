# Yayın Kapısı — Respected Brain

Durum: **Windows x64 için doğrulandı**; macOS, Linux ve WSL doğrulanmadı. Authenticode uygulanmadı.
Bu belge `0.1.0-beta.1` (`0.1.0b1`) yayın paketinin hangi kapılardan geçtiğini ve neyin kapsam dışı olduğunu kaydeder.

## Kapı matrisi

| Kapı | Durum | Kanıt |
|---|---|---|
| Tam birim ve entegrasyon testleri | GEÇTİ | `python -m unittest discover -s tests -t .` → 1028 test OK, 15 skip |
| Şema migration ve eski sürüm fixture'ları | GEÇTİ | `python -m unittest tests.installation.test_migrate -v` → 6 test OK; `tests/fixtures/releases/0.1.0-beta.1/` |
| Dondurulmuş Windows paketi | GEÇTİ | `python packaging/build_dist.py --platform windows --output dist` → `0.1.0b1` |
| Dağıtım bütünlüğü | GEÇTİ | `python -m unittest tests.packaging.test_distribution -v` → 3 test OK |
| Fiziksel kurulum smoke'u | GEÇTİ | `tests/evals/results/br015-native-smoke.json` → 25/25 VERIFIED, `overall=VERIFIED` |
| Hub ortak sözleşme conformance'ı | GEÇTİ | Hub deposunda `python -m unittest discover -s common/conformance -v` → 9 test OK; üç ürünün sözleşme kopyasını denetler |
| Authenticode | UYGULANMADI | Sertifika yok; imzasız paket başarılı imza sayılmaz |
| macOS / Linux / WSL | DOĞRULANMADI | Kod ve betikler var; derleme, kurulum ve smoke bu ortamlarda çalıştırılmadı |

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
- Kod imzası olmadığı için SmartScreen uyarısı beklenir; Authenticode kapısı açık kalır.

## Yeniden üretim

```powershell
python -m unittest discover -s tests -t .
python packaging/build_dist.py --platform windows --output dist
python -m unittest tests.packaging.test_distribution -v
python tests/native/smoke/platform_smoke.py --package dist/RespectedBrain --output tests/evals/results/br015-native-smoke.json
```

Hub ortak conformance'ı, Hub deposunun kökünde `python -m unittest discover -s common/conformance -v` ile çalıştırılır.
