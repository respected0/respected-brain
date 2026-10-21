# Respected Brain kaynak deposu çalışma kuralları

Proje gerçeğini güncel dosyalardan doğrula. Onaylı tasarım `docs/decisions/`, aktif ürün durumu yalnız
`docs/PROJECT_STATUS.md` içindedir. Bu bilgisayara özel devreye alma kararı Git dışındaki `.local/ROLLOUT.md` kaydındadır.
Kullanıcının canlı programını veya not kasasını kaynak işi sırasında değiştirme.

## Değişiklik disiplini

- Kod değişince ilgili rehber, karar ve durum belgesini aynı değişiklikte güncelle; hedefi uygulanmış, uygulanmışı
  doğrulanmış diye yazma.
- Testler `tests/` altında `src/respectedbrain` ile aynı alana konur (`test_*.py`); ortak sahteler `tests/support/`.
  `python -m unittest discover -s tests -t .` geçmeden tamamlandı deme. Test paketi HOME'u geçici klasöre yönlendirir;
  bunu atlatan test yazma.
- Paket değişikliğinde `tools/build_installer.py` ile build al ve `tools/verify_distribution.py` ile doğrula.

## Kaynak ve kurulu ürün sınırları

Ürün kodu `src/respectedbrain/`, immutable hazır içerik `resources/`, paket tarifleri `packaging/`, geliştirici araçları
`tools/` altında kalır. AppRoot, DataRoot ve VaultRoot birbirinden ayrıdır. Güncelleme/kaldırma insan notlarını üzerine
yazmaz; sahiplik, işlem günlüğü ve geri alma korumaları korunur.

## Push sonrası CI takibi

Kullanıcı tercihi (2026-10-05): push sonrasında CI sonucunu sürekli sorgulayarak bekleme; bunun için ajan veya otomasyon
başlatma. Sonuç çıktığında kullanıcı yeniden çağırır, o çağrıda sonucu incele. Doğrulanmamış CI sonucunu başarılı bildirme.

## Belge düzeni

Süreç aracı adı taşıyan repo/yerel klasör kullanılmaz. Kararlar `docs/decisions`, kullanım rehberleri `docs/guides`,
geliştirici belgeleri `docs/development` altındadır; tarihli çalışma kayıtları tutulmaz (Git geçmişi yeterlidir). Yerel
ikili yedek ve test kanıtları `.local/archives` içindedir. Kullanıcı istemedikçe paralel ajan çalıştırma.
