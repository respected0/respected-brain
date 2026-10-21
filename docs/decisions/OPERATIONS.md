---
title: Respected Brain — Kurulum Sözleşmeleri
created: 2026-10-03
scope: project
confidence: inferred
supersedes: []
status: written-spec-approved
timeline:
  - from: 2026-10-03
    until: 2026-10-03
    learned: Yazılı sözleşme kullanıcı incelemesini bekliyordu; kullanıcı onayladı.
    source: "the human partner reviews and approves the written spec"
---

> Onaylı kurulum sözleşmesi (2026-10-03), 2026-10-21 itibarıyla Hub üzerinden kurulan dondurulmuş pakete göre güncellendi. [Aktif durum](../PROJECT_STATUS.md).


# Kurulum Sözleşmeleri

Program/veri/kasa konumları ve modül sınırları [mimaride](../ARCHITECTURE.md) yaşar; burada komut, kurulum,
veri koruma ve kabul koşulları tanımlanır.

## 1. Tek CLI ve entegrasyon sözleşmesi

Ürün komutları aynı paket dağıtıcısını kullanır:

```text
respectedbrain setup --vault <path>
respectedbrain configure
respectedbrain vault register|list|discover
respectedbrain open --vault-id <id>
respectedbrain hook --provider <name> --event <event> --vault-id <id>
respectedbrain mcp --vault-id <id>
respectedbrain briefing --vault-id <id>
respectedbrain compile --vault-id <id>
respectedbrain update --package <path>
respectedbrain repair --vault-id <id>
respectedbrain uninstall
```

Kasaya bağlı komutlar UUID yerine açık `--vault <path>` de kabul eder.
Hook'lar mevcut transcript/session argv ve stdin alanlarını provider
adaptörüyle korur. Event normalizasyonu oturumun idempotency anahtarını
değiştirip eski konuşmayı tekrar kaydetmez.

Global hook, MCP, zamanlayıcı ve kısayol mevcut `respectedbrain` başlatıcısını
çağırır. `.py` dosyasının kurulu konumunu, sistem Python'ını veya
`runtime/scripts` yolunu sabitlemez. Native Windows `.exe`, POSIX kurulum
native CLI kullanır. WSL seçilmişse kayıt sırasında WSL içinde mevcut
başlatıcı doğrulanır ve Windows/WSL sınırındaki argv yolları dönüştürülür;
Linux Python'a Windows dosya yolu verilmez. WSL olmayan Windows kurulumda
WSL varsayılan bağımlılık olmaz.

Global/MCP/zamanlayıcı seçenekleri tek desired-state kaydından okunur.
Kapalı özellik repair veya update tarafından açılmaz. Harici
ayar dosyalarında yalnız sahipli bölüm güncellenir, mevcut kullanıcı
ayarları korunur, önce yedek alınır. Her harici kayıt başlatıcı ve kasa
kimliğini içerir. Native hook/MCP protokol stdout'u logla kirletilmez.

Bir geçiş sürümü boyunca eski komut başlatıcıları gerekirse ince uyumluluk
sarmalayıcısı kalabilir. Ürün mantığı içermez; yeni CLI'a aktarır ve çıkış
kodunu korur. Yeni paket ikinci eski motor ağacı taşımaz.

## 2. Template ve kullanıcı özelleştirmesi

Yeni kasa oluşturma: paket resources/vault-template okunur, profil
yer tutucuları doldurulur, geçici stage doğrulanır ve hedefe aktarılır.
Hedef dolu ve kasa olarak kayıtlı değilse hiçbir dosya değiştirilmez.
Var olan kasa update işleminde template yeniden kopyalanmaz.

`📋 Templates` ve `.obsidian` kopyalandıktan sonra kullanıcı içeriğidir.
Kullanıcı düzenlemeleri program kaynaklarıyla senkronize edilmez.
Kullanıcının Companion/Core/Kurallar/Last-Session/Threads/Journal dosyaları
paket instructions dosyasından yeniden üretilmez.

Paket instructions/skills varsayılanları immutable kaynaklardır. Güncel
vault kimliği ve tercihleri global entegrasyon render sırasında bağlama
eklenir. Kullanıcının mevcut kişiselleştirilmiş motor instructions/skills
dosyaları varsa yalnız paketle birebir aynı olanlar varsayılan sayılır;
farklı olanlar DataRoot/vaults/<id>/overrides altında korunur ve render
önceliğinde paket varsayılanını geçer. overrides çalışma state'i değildir.

## 3. Kurulum, güncelleme, onarım ve kaldırma

### Yeni kurulum

Platform kabuğu tek AppRoot paketini stage edip doğrular. Ortak setup
hizmeti kasa yaratma/kayıt, kullanıcı config'i ve seçilmiş entegrasyonları
uygular. İşlem sonunda AppRoot, DataRoot, VaultRoot sözleşmesi doğrudan
oluşur.

Windows'ta bu adımları Respected Hub çalıştırır: imzalı paketi doğrulayıp stage eder, sonra ürünün kendi
`setup`/`update`/`repair`/`uninstall` komutunu çağırır. Bağımsız kurucu yoktur; kasa ayrı kullanıcı seçimidir.

### Güncelleme

Yeni paket ayrı stage edilir, kaynaklar/importlar/CLI sağlığı doğrulanır.
Aktif yazıcılar durdurulur ve işlem kilidi alınır. Eski sahipli uygulama
dosyaları yedeklendikten sonra yeni paket etkinleştirilir. İnce launcherlara
bağlanan harici kayıtlar gerektiğinde aynı işlemle yenilenir. Sağlık veya
entegrasyon hatasında eski program ve değişmiş harici kayıtlar geri alınır.

Özel atomik dizin değişimi varsayılmaz: Windows'ta açık executable dikkate alınır (çalışan program kendini
ertelenmiş yardımcıyla günceller); manifest/journal ile doğrulanabilir
stage, activation ve rollback uygulanır. Kasa notları bu işlemin payload'ı
değildir. Config şema dönüşümü varsa kendi yedeği ve rollback'i vardır.
Uygulama klasörü sürümlere göre çoğaltılmaz; kalıcı ikinci aktif motor yoktur.

### Onarım

Paketin sahipli kaynakları ve seçilmiş bağlantılar doğrulanır; kullanıcı
notları üzerine template yazılmaz. Cache gerektiğinde yeniden üretilebilir.
Çıkış kodu bir alt işlem başarısızken başarı sayılmaz.

### Kaldırma

Yalnız uygulama manifestindeki eşleşen paket dosyaları ve eşleşen harici
kayıtlar kaldırılır. Varsayılan olarak DataRoot korunur. Not kasası korunur.
Geniş `DelTree(DataRoot)` veya `vault.glob('*.py')` temizliği kullanılmaz.
Kullanıcı tarafından değiştirilmiş harici kayıt başka uygulamayı silecek
şekilde kaldırılmaz; sahiplik uyuşmazlığı bildirilir.

## 4. Kabul kriterleri

- Kaynakta tek `respectedbrain` paketi; kurulumda tek aktif motor dağıtımı.
- Wheel/frozen paket kaynakları ve template dahil; repo checkout'una bağımlı değil.
- Program salt okunur hedefte çalışır; AppRoot'a teknik veri yazmaz.
- Yeni kasa scripts, engine, kaldırıcı veya arama DB'si içermez.
- Install/update/repair CLI ve platform kabuklarından aynı son yerleşimi üretir.
- Hook/compile/briefing/search/MCP aynı AppPaths ve UUID'yi kullanır.
- Farklı CWD, Türkçe/emoji/boşluklu yollar, seçilmiş kasa, iki kasa ve kasa
  yer değiştirme senaryolarında yanlış kasaya fallback olmaz.
- Native Windows ve açık WSL profillerinde başlatıcı/yol sözleşmeleri test edilir.
- Kapalı global/MCP/zamanlayıcı seçeneği geçişten sonra kapalı kalır.
- Gerçek kullanıcı config'i ve kişiselleştirilmiş instructions/skills korunur.
- Çakışan state, yazıcı yarışı ve her aşamada enjekte edilmiş arıza rollback
  davranışıyla test edilir; kullanıcı sentinel dosyaları korunur.
- Update/uninstall sırasında örnek daily, knowledge, Companion,
  proje notları ve `.obsidian` kullanıcı dosyalarının hash'leri değişmez.
- Paket tests, kaynak tests ve Windows kurulum/geri alma/harici kayıt testleri
  geçer. Atlanan platform doğrulaması açıkça raporlanır.

## 5. Yedekten geri yükleme (restic, isteğe bağlı)
`respectedbrain maintenance backup_restic --repo REPO --restore-to YENI_BOS_KLASOR [--snapshot ID] [--password-file DOSYA]`: anlık görüntüyü
yeni veya boş, vault'un dışındaki bir klasöre geri yükler; vault'un üzerine hiçbir şey yazılmaz, gerekenleri siz geri kopyalarsınız. Yedekleme
parola kaynağı ister, yeni depoyu başlatır ve yedeği geri yükleyip her dosyanın SHA-256 değerini karşılaştırarak doğrular. Ayrıntı:
`PRIVACY_AND_CLIENT_CONFIG.md`.

### Gerçek restic doğrulaması (2026-10-18, restic 0.19.1, Windows)
Düz `restic restore <id>` Windows'ta `C:\Users\...` yolunu yeniden kurar ve salt-okunur sistem klasörlerinin zaman damgasını yazamayıp hata verir (hedef de silinemez hale gelir). Bu yüzden geri yükleme ve doğrulama `restic restore <id>:/C/yol/vault` biçimini kullanır; yalnızca vault içeriği hedefe iner. İlk yedek (init), parola dosyası, Türkçe dosya adı, içerik doğrulaması, boş olmayan/vault içi hedef reddi ve bozulmuş paket tespiti gerçek restic ile geçti.
