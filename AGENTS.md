# Respected Brain deposu: çalışma kuralları

Gerçeği kod ve testlerden doğrula. Belgeler: `README.md` (giriş), `docs/USAGE.md`, `docs/COMMANDS.md`, `docs/ARCHITECTURE.md`.
Üç ürünün ortak sözleşmesi `docs/PRODUCT_CONTRACT.md` dosyasındadır ve Hub deposundaki `common/conformance/` ile ölçülür (üç depo yan yana).

## Yasaklar

- Kişinin kurulu programını, gerçek not kasasını ve AI araçlarının gerçek ayarlarını değiştirme.
- Global araç kurma. Kullanıcı istemedikçe commit, push ya da paralel ajan yok.
- Geçiş dönemi, eski sürüm desteği, takma ad ya da uyumluluk katmanı ekleme: bir şey değişiyorsa her yerde değişir.

## Sınırlar

- Program dosyaları kurucunundur (`packaging/windows/brain_setup.iss`; Orchestrator kurucusunun ortak bölümü
  buradan üretilir). Ürün `setup`, `repair`, `uninstall [--purge]`, `config`, `health`, `rpp`, `mcp` ile kaydı, veriyi,
  kasayı ve bağlantıları yönetir. `update` komutu, kendini güncelleme ve protokol üzerinden kurma yoktur.
- Kişinin ayarlarının tek kaynağı `src/respected_brain/settings.py`; RPP, `config` ve kurucu (`--set`) aynı kodu kullanır.
- Program, veri ve kasa kökleri ayrıdır. Kaldırma ve onarım insan notlarının üzerine yazmaz; sahiplik kaydı, işlem
  günlüğü ve geri alma korunur.
- Kaynak `src/respected_brain/`, değişmez paket içeriği `src/respected_brain/resources/`, paket tarifleri `packaging/`.

## Değişiklik disiplini

- Testler `tests/` altında `src/respected_brain` ile aynı alanda (`test_*.py`); ortak sahteler `tests/support/`. Test
  takımı HOME'u geçici klasöre yönlendirir; bunu atlatan test yazma.
- Tamamlandı demeden önce: `python -m unittest discover -s tests -t .`. Paket değişikliğinde
  `python packaging/build_dist.py --platform windows --output dist` ve `python -m unittest tests.packaging.test_distribution`.
- Kod değişince ilgili belgeyi aynı değişiklikte güncelle. Hedefi uygulanmış, uygulanmışı doğrulanmış diye yazma.
  Belgeler Türkçedir; tarihli çalışma kaydı tutulmaz (Git geçmişi yeterli). Testler belge cümlelerine bağlanmaz.
- Push sonrasında CI sonucunu sorgulayarak bekleme; kişi yeniden çağırınca incele. Doğrulanmamış CI'ı başarılı bildirme.
- Süreç aracı adını taşıyan klasör açma. Yerel ikili yedek ve kanıtlar `.local/archives` içinde, Git dışında.
