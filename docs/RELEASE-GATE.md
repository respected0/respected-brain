# Yayın Kapısı — Respected Brain

Durum: **Windows x64 ve WSL2 üzerinde Linux x64 dondurulmuş paketleri için doğrulandı**; macOS, bare-metal Linux ve uzak CI doğrulanmadı. Authenticode uygulanmadı.
Bu belge `0.1.0-beta.2` (`0.1.0b2`) yayın paketinin hangi kapılardan geçtiğini ve neyin kapsam dışı olduğunu kaydeder.

## Kapı matrisi

| Kapı | Durum | Kanıt |
|---|---|---|
| Tam birim ve entegrasyon testleri | GEÇTİ | Windows 11 x64: 1078 test OK, 21 skip (2026-11-05, 386.526 sn); WSL2 Ubuntu 26.04 / Python 3.14.4: 1073 test OK, 32 skip (2026-11-05, 275.888 sn, BR-032 öncesi); EXIT=0 |
| Şema migration ve eski sürüm fixture'ları | GEÇTİ | `python -m unittest tests.installation.test_migrate -v` → 6 test OK; `STEPS` yalnızca gerçek boşlukları içerir; `tests/fixtures/releases/0.1.0-beta.1/` |
| Dondurulmuş Windows paketi | GEÇTİ | `python packaging/build_dist.py --platform windows --output dist` → `0.1.0b1` |
| Dondurulmuş Linux paketi | GEÇTİ | WSL2 Ubuntu'da `python3 packaging/build_dist.py --platform linux --output dist-linux` → `0.1.0b1`; `tests/evals/results/br030-linux-smoke.json` → 25/25 VERIFIED, `overall=VERIFIED` |
| Dağıtım bütünlüğü | GEÇTİ | `python -m unittest tests.packaging.test_distribution -v` → 3 test OK |
| Fiziksel kurulum smoke'u | GEÇTİ | `tests/evals/results/br015-native-smoke.json` → 25/25 VERIFIED, `overall=VERIFIED` |
| MCP dizin izleyicisi | GEÇTİ | `py -m unittest tests.search.test_watch -v` → 5 test OK; uzun ömürlü MCP süreci ~1 sn yoklamayla FTS dizinini tazeler, ayrı süreç/servis yoktur |
| Hub ortak sözleşme conformance'ı | GEÇTİ | Hub deposunda `python -m unittest discover -s common/conformance -v` → 9 test OK; üç ürünün sözleşme kopyasını denetler |
| Authenticode | UYGULANMADI | Sertifika yok; imzasız paket başarılı imza sayılmaz |
| macOS / Linux / WSL | KISMEN | Windows x64 ve WSL2 üzerinde Linux x64 dondurulmuş paketleri doğrulandı (BR-030); Ubuntu kaynak testi ve Linux frozen build/smoke job'ları CI matrisinde (BR-026/BR-031). macOS gerçek donanım, bare-metal Linux ve uzak CI doğrulanmadı |

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

### Linux/WSL2 dondurulmuş paket smoke'u

WSL2 Ubuntu (`Linux 6.18.33.2-microsoft-standard-WSL2`, glibc 2.43, Python 3.14.4) üzerinde Linux x64 dondurulmuş paket üretildi ve geçici kurulum köklerinde 25 kontrolün tamamı doğrulandı. Kapsam: temiz kurulum, dondurulmuş başlatıcı, onarım, beş sağlayıcı kaydı, hook, arama, MCP, flush, kaldırma/yeniden kurulum ve veri koruma.

Smoke, yaşam döngüsü sürücüsü `respected_brain` paketini içe aktarabilsin diye izole bir sanal ortamda çalıştırıldı; bu yalnızca test koşum ortamıdır, paket bağımlılığı değildir. Kanıt: `tests/evals/results/br030-linux-smoke.json` → 25/25 `VERIFIED`. WSL2 sonucu bare-metal Linux veya başka bir dağıtımın kanıtı değildir.

## Yayın kararı

- Windows x64 ve WSL2 üzerinde Linux x64 dondurulmuş paketleri için test ve veri bütünlüğü kapıları geçti.
- MCP süreci açıkken dizin değişiklikleri ~1-2 sn içinde FTS dizinine girer; MCP kapalıyken sorgu öncesi, oturum ve günlük görev tazelemesi geçerlidir.
- Çok platformlu yayın kapısı geçmedi; macOS, bare-metal Linux ve uzak CI doğrulanmamış sayılır.
- Üretim kod imzalama sertifikası olmadığı için SmartScreen uyarısı beklenir; Authenticode kapısı açık kalır.

## Açık dış bağımlılıklar

BR-029 denetiminde kalan maddeler yeniden kontrol edildi; bunlar kod hatası değil, dış kaynak, donanım veya gerçek üretim kimliği gerektiriyor:

| Madde | Gerçek durum | Neden açık |
|---|---|---|
| Authenticode | `signtool` kurulu değil; kullanıcı deposunda yalnızca `CN=Respected Test Signer` self-signed test sertifikası var | Üretim kod imzalama sertifikası yok; test sertifikası SmartScreen güveni sağlamaz |
| OpenRouter gerçek çağrı | `credential status` → `configured=true`, `protection=dpapi`; ücretsiz modelle gerçek çağrı başarılı; kullanım defterine `cost: 0.0` yazıldı; `auto` modda ücretli kapı testlerle kapalı | Sıfırdan büyük gerçek maliyet bakiye gerektirir, görülmedi |
| macOS | Gerçek macOS donanımı yok | Yalnızca platform simülasyonları çalışıyor |
| Bare-metal Linux / diğer dağıtımlar | Yalnızca WSL2 Ubuntu üzerinde Linux x64 dondurulmuş paket doğrulandı | Fiziksel Linux makinesi ve diğer dağıtımlar denenmedi |
| Uzak CI | `.github/workflows/ci.yml` içinde Windows native/source, Ubuntu source ve Linux frozen build/smoke job'ları tanımlı | GitHub Actions üzerinde çalıştırılmadı; yerel Linux sonucu CI kanıtı değildir |

## Yeniden üretim

```powershell
python -m unittest discover -s tests -t .
python packaging/build_dist.py --platform windows --output dist
python -m unittest tests.packaging.test_distribution -v
python tests/native/smoke/platform_smoke.py --package dist/RespectedBrain --output tests/evals/results/br015-native-smoke.json
```

Linux x64 dondurulmuş paket WSL2 içinde üretilir ve smoke edilir:

```bash
python3 packaging/build_dist.py --platform linux --output dist-linux
python tests/native/smoke/platform_smoke.py --package dist-linux/RespectedBrain --output tests/evals/results/br030-linux-smoke.json
```

Smoke, `respected_brain` paketini içe aktarabilen izole bir Python ortamında çalıştırılmalıdır.

Hub ortak conformance'ı, Hub deposunun kökünde `python -m unittest discover -s common/conformance -v` ile çalıştırılır.
