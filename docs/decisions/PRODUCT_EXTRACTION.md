# Respected ürün ayrımı — uygulama kararı

scope: project; date: 2026-10-09; confidence: user-directed

Kullanıcının EXECUTE PRODUCT EXTRACTION talimatı uygulama kapsamıdır. Git işlemi,
canlı kurulum, kullanıcı kasası veya sağlayıcı ayarlarında değişiklik yapılmaz.
Yeni kardeş kaynaklar `../respected-orchestrator` ve `../respected-hub` olur;
dördüncü ortak depo kurulmaz. Brain bellek özellikleri korunur.

Orchestrator Python standard library ile bağımsız DataRoot ve proje seçimi kullanır.
Mevcut generic CLI eşleştirmeleri ve Antigravity lane/scope/brief/patch bileşenleri
taşınır. Hub Tauri 2 + React + TypeScript ile özel JSON engine girişini kullanır;
motorun çalışması Hub ömrüne bağlanmaz. İlk sürüm yerel ürün keşfidir, üretim
kurulum/güncelleme desteği diye sunulmaz.

## Bu uygulamanın sırası ve kabul kapıları

1. İki kaynak kimliğini, testleri ve özellik sahipliği kaydını oluştur.
2. Brain importu olmayan motoru çıkar; explicit scope, worker/test deadline,
   süreç ağacı sonlandırma, iptal, başarısız/stale/tampered sonuç reddi testlerini
   geçici projelerde çalıştır. Önce RED, sonra gerçek worker ile GREEN.
3. Hub ürün durumu, proje seçimi, task gönderme, status/log/result/cancel akışını
   engine JSON girişine bağla; TypeScript/web build ve mümkünse native Tauri test et.
4. Ancak Hub ve taşınan bütün özellikler doğrulandığında Brain orchestration ve
   dashboard dağıtımını kaldır. Eksik eşdeğer varken mevcut kod korunur.
5. Kalan hardening işlerini ürün sahibine bağla; tarihsel F1–F15'i yeniden çözmeye
   girişme. RPP/SIL/finite lifecycle, sahiplik/crash recovery ve güvenli dağıtım
   hedeflerini koru; uygulanmış diye etiketleme.

Scope kontrolü OS sandbox yerine geçmez. Yerel engine hesabın yetkileriyle
çalışır; provider varsayılan izinleri atlanmaz. Yazma görevi için bağımsız
doğrulama komutu gerekir. Sonuçlar yalnız inceleme içindir; otomatik apply yoktur.
Native Rust/C++ araçları yoksa global kurulum yapılmaz, somut engel kayda geçer.

Yeni kaynakların atlasları, Brain atlası ve anlamlı regresyon testleri kapanış
kapısıdır. Uygulama kanıtı `docs/records/2026-10-product-extraction/` altında;
aktif durum yalnız `docs/PROJECT_STATUS.md` içinde tutulur.
