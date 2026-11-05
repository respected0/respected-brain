# Respected Brain — Yol Haritası: Beta.2 yayın doğrulamasından V1.0'a

> **Belge sürümü:** Plan 1.0 — 5 Kasım 2026; depo durumu 6 Kasım 2026'da koda ve belgelere karşı denetlendi (A.5).
> **Durum:** Ürün sahibi tarafından onaylanan hedef kapsam; geliştirme ve testlerin tamamlandığı iddia edilmez.
> **Amaç:** Beta.2 yayın öncesi doğrulamasından V1.0'a kadar bütün görevleri, kabul kriterlerini, rakip ve araştırma referanslarını tek kalıcı belgede tutmak.
> **İşaretleme kuralı:** Bu belgede tamamlanan madde silinmez; kod, test ve kanıt bağlantısıyla `[x]` yapılır. Kanıtsız madde `[x]` olmaz.


## A. BELGENİN STATÜSÜ, KULLANIMI VE GERÇEKLİK KURALLARI

### A.1. Kesin ürün sahibi kararları — değiştirilemez kapsam

1. **Brain'in temel işi:** AI coding oturumlarından güvenilir hafıza **almak → saklamak → güncellemek → doğru zamanda geri vermek**.
2. **Beta.2:** Geliştirme tamamlanma aşamasında kabul edilir; baştan yeniden yapılmaz. İlk iş **yayın öncesi mini doğrulama** ve bulgulara göre yayın kararıdır.
3. **Beta.3:** Respected Brain, Hub'dan bağımsız **kendi masaüstü uygulaması** olur. UI teknolojileri **Tauri 2 + React + TypeScript**, hafıza motoru **Python**. Bu sürümde motor Rust'a taşınmaz.
4. **Ekosistem:** Hub Tauri/Rust motorludur; Orchestrator için Tauri 2 + React + TypeScript arayüzü ve Python motoru planlıdır. Brain tek başına kurulur/çalışır; Orchestrator'ın orkestrasyon sorumluluğunu devralmaz.
5. **Beta.4:** Rakipler yeniden araştırılır; **rakiplerin bütün ilan edilmiş özellikleri tek tek envantere alınır**. Brain'in alanına giren tüm hedef hafıza yeteneklerine işlevsel eşitlik veya daha iyi davranış amaçlanır. Başka ürünün alanındaki özellikler de **kaybolmadan** kataloglanır ve gerekçeli mimari karar verilir.
6. **Beta.5:** **10/10 özellik kesin hedef kapsamdır** (Bölüm F). Beta.4 altyapısı üzerine geliştirilir, sadece fikir olarak bırakılmaz.
7. **Beta.6:** Beta.5 dahil tüm özellikler literatür, tutarlı karşılaştırmalı deneyler, gerçek kullanıcı/geliştirici testleri ve güvenlik testleriyle optimize edilir. Araştırma, test ve güvenlik beta.6'yı beklemeden tüm sürümlerde de yapılır.
8. **Beta.7:** Özellik dondurma, bug fixing, güvenlik, kullanılabilirlik, veri taşıma, yük ve dağıtım sertleştirmesi.
9. **Beta.8+ / RC:** Gerekirse ilave yalnızca düzeltme sürümleri; kararlı ilk yayın **V1.0**. 'Sıfır hata' kanıtlanamaz; bilinen P0/P1 hatası 0 olmalı ve kalan riskler belgelenmelidir.
10. **Görsel/UX iyileştirmeleri tüm betalar boyunca yapılır**; her yeni yetenek kendi UI, erişilebilirlik, izin, hata ve boş-durum tasarımıyla teslim edilir.
11. **V1.0 vaadi:** Kullanıcının sahip olduğu, açıklanabilir, taşınabilir, denetlenebilir ve agent'lar arası çalışabilen hafıza.
12. **Kapsam büyüklüğü nedeniyle iş yükü kaybolmaz:** Beta.4 ve beta.5 için alt iş paketleri, milestone ve sürüm adayı kullanılabilir; ancak bu 10 onaylı özelliği veya seçilen rakip hafıza yeteneklerini sessizce gelecek sürüme itme izni değildir. Kapsam değişikliği ürün sahibinin açık kararıyla kaydedilir.

### A.2. Gerçek durum — 5 Kasım 2026 depo belgesine dayanan kontrol noktası

- Kaynak: [Respected Brain](https://github.com/respected0/respected-brain), [ROADMAP](https://github.com/respected0/respected-brain/blob/main/docs/ROADMAP.md), [ROADMAP-EXECUTION](https://github.com/respected0/respected-brain/blob/main/docs/ROADMAP-EXECUTION.md), [ARCHITECTURE](https://github.com/respected0/respected-brain/blob/main/docs/ARCHITECTURE.md), [RELEASE-GATE](https://github.com/respected0/respected-brain/blob/main/docs/RELEASE-GATE.md).
- GitHub Releases taramasında yayımlanmış sürüm `0.1.0-beta.1` görünmektedir. Beta.2 geliştirmesi ve test çalışmaları repo belgelerinde ilerlemiştir; **beta.2 yayınlanmış varsayılmaz**.
- Önceki görevler `BR-001` … `BR-018` yürütme günlüğünde tamamlanmış/uygulanmış kayıtlıdır. **Bu iddia gerçek kullanıcı ortamında hepsinin eksiksiz doğrulandığı anlamına gelmez.** `BR-019` çoklu OS gerçek doğrulama ve `BR-020` ileri yetenekler açıktır.
- BR-011 sentetik FTS5 değerlendirmesi: 50 senaryoda başlangıç %64, devam değerlendirmesi %94; temporal kategori 7/10, update 10/10. Bu **kendi sentetik veri setindeki sonuçtur**, bağımsız/gerçek hayat/rakip üstünlüğü iddiası değildir.
- BR-012 ayrı uzun-not fixture'ında kademeli geri çağırma başarısı yüksek raporlanmıştır; değerlendirme ortamının ölçüm sınırları korunacaktır.
- BR-017 OpenRouter, mock ve anahtarsız durumlarda test edilmiştir; **gerçek ücretli API çağrısı ve maliyeti doğrulanmamıştır**. OpenCode için gerçek oturum/köprü kanıtı ile modelin gerçekten hafızayı kullanması ayrıdır.
- `docs/ROADMAP.md` eski ifadeler içerebilir (ör. OpenRouter hâlâ yok diye anlatılıyor); **fiili kod + execution kanıtıyla karşılaştırıp düzelt**, orijinal tarihi silme.
- `docs/RELEASE-GATE.md` yayımlanmış beta.1'in Windows x64 doğrulamasına ilişkindir; beta.2 için **yeni rapor** gerekir. Geçmiş `1028 test OK, 15 skip` sayısını beta.2'ye otomatik kopyalama.
- Bu belge **canlı test çalıştırıldığına dair kanıt değildir**. Repo dosyaları ve yayımlanmış teknik belgeler incelenmiş, plan buna göre hazırlanmıştır. Görev durumu kodu ve test raporu ile doğrulanmadan `[x]` yapılmaz.

### A.3. Mevcut yapıda korunacak sözleşmeler

- Program kökü, veri kökü ve kullanıcının seçtiği Markdown/Obsidian kasası **üç ayrı kök** olarak kalır. Kasa `.respected.json` UUID'si ve şema tanımı üzerinden tanımlanır; kasaya uygulama dosyası, kullanıcı makinesine özel yol veya arama DB'si yazılmaz.
- Notlar düz Markdown'dır; kullanıcıya aittir. Kurulum, yükseltme, onarım ve kaldırma **kullanıcı notlarını silmez**.
- Mevcut Python modül sınırlarını (`core/`, `vault/`, `memory/`, `search/`, `providers/`, `integrations/`, `installation/`, `rpp/`, `maintenance/`) koru; değiştirme gerekiyorsa ADR yaz.
- `mcp_write` varsayılan **kapalı** ve her çağrıda kontrol edilir. Gelen MCP notları yalnızca izinli Inbox'a, `review: pending` ve doğru kaynak etiketiyle yazılır; model kendini `verified` ilan edemez.
- `archive_transcripts` varsayılan **kapalı**. Açık ise maskelenmiş, saklama süreli, veri köküne yazılan arşiv. Yeni masaüstü uygulaması bu varsayılanı gizlice değiştiremez.
- Dış kaynak metin, prompt veya hafıza gövdesi **yetkili talimat değildir**. RPP yetkileri, güvenli yol çözümleme, symlink/TOCTOU korumaları, atomik yazma, hash ve kilitler korunur.
- İzinli sağlayıcı seçimi ve maliyet sınırı: kendiliğinden ücretli API'ye geçme yok; sağlayıcıya veri aktarımı ayrıca görünür/izinli.
- Brain CLI/MCP/RPP işlevleri **Tauri penceresine bağlı olmamalı**. Kullanıcı UI'yı kapatınca hafıza kaybolmaz; agent'dan çağrılırken gerekirse process on-demand başlar.
- Orchestrator görevleri/agent yürütmesini yönetir; Brain bilgi ve aktarım paketi sağlar. Hub ekosistem katalog/entegrasyon alanını yönetebilir ama Brain'in çalışması için zorunlu değildir.
- Yetkili protokol/ürün sözleşmesi değişirse ilgili uygulamaların conformance testleri beraber güncellenir; `PRODUCT_CONTRACT.md` ile çelişen ikinci bağımsız sözleşme oluşturulmaz.

### A.4. Uygulama/kanıt durum sözlüğü

- `PLANNED`: Onaylı, uygulanmamış hedef.
- `EXISTING-VERIFY`: Kodda/mevcut belgede var; regresyon ve gerçek kullanım kontrolü gerekli.
- `PARTIAL`: Alt akış veya arayüz eksik.
- `IMPLEMENTED-TESTED`: Kod + test kaydı var; gerçek ortam kanıtı eksik olabilir.
- `REAL-VERIFIED`: Tanımlı gerçek ortam/istemci/sağlayıcıda çalışmış, artefakt saklanmış.
- `COMPETITOR-DOCUMENTED`: Rakibin kendi dokümanında var, bağımsız test edilmemiş.
- `EVIDENCE-OPTIMIZED`: Başlangıç/sonuç, deney protokolü ve istatistiksel sınırlama kayıtlı.
- `DEFERRED-EXPLICIT`: Yalnız ürün sahibinin kayıtlı kapsam kararıyla başka sürüme alınmış.

> **Tekrarlanan geliştirmeyi engelle:** Önce her görevde `code_exists → tests_exist → evidence_exists → UX_exists → acceptance_met` denetimi yap. Var olan BR-001…BR-018 kodunu aynı amaçla ikinci kez yazma; fark işini aç.

### A.5. Depo durumu — 6 Kasım 2026, koda ve belgelere karşı doğrulandı

- `pyproject.toml` sürümü `0.1.0-beta.2`; Git'te yalnız `v0.1.0-beta.1` etiketi var. **Beta.2 yayınlanmadı**, aşağıdaki B2 görevleri yayın öncesi kapıdır.
- [RELEASE-GATE.md](RELEASE-GATE.md) beta.2 paketi için bir kapı matrisi taşır (Windows 11 x64: 1078 test OK, 21 skip; WSL2 Ubuntu: 1073 OK, 32 skip; fiziksel smoke ve Linux smoke kanıtı; Authenticode uygulanmadı). Bu kayıt B2 görevlerinin kanıtıdır; ayrı `beta2-release-evidence` raporu (B2-G00) henüz yoktur ve B2 maddeleri bu yüzden `[ ]` kalır.
- `docs/ROADMAP-EXECUTION.md` depoda yoktur. `BR-*` kayıtları [ARCHITECTURE.md](ARCHITECTURE.md), [BASELINE.md](BASELINE.md) ve `docs/evidence/` içinde kalır; eski `BR-001`…`BR-018` kanıtı silinmedi.
- `BR-019` (çoklu OS): Linux x64 dondurulmuş paketi WSL2'de doğrulandı (`BR-030`, `docs/evidence/br030-linux-smoke.json`); macOS, bare-metal Linux ve uzak CI doğrulanmadı → **açık**.
- `BR-020` (ileri yetenekler): depo belgelerinde bu kimlikle kayıt bulunamadı → **açık**, K.1 eşlemesine göre B4/B5'te izlenir.
- Eski `ROADMAP.md` "Henüz madde yok" diyordu; OpenRouter/OpenCode gibi uygulanmış konularla çelişen bir ifade kalmadı.


---

## B. SÜRÜMLER VE AŞAMA KAPILARI

| Sürüm | Ürün teslimatı | Yayını bloke eden durum |
|---|---|---|
| `0.1.0-beta.2` | Güvenilirlik çekirdeğinin son mini doğrulaması | Kasa kaybı/izinsiz yazma, kritik test regresyonu, yanlış destek iddiası |
| `0.1.0-beta.3` | Bağımsız Tauri 2 + React + TypeScript Brain uygulaması, Python core | Hub zorunluluğu, yanlış kasaya bağlanma, UI kapatılınca CLI/MCP'nin bozulması |
| `0.1.0-beta.4` | Rakip yetenek envanteri ve hedef hafıza eşitliği, Desktop UI | Envanterde hedefsiz çekirdek hafıza yeteneği, kritik test olmaması |
| `0.1.0-beta.5` | **10/10** ayırt edici yetenek uygulandı | On özellikten birinin işlevsel kabul kriterini geçmemesi |
| `0.1.0-beta.6` | Araştırma, gerçek kullanım, güvenlik ve performans kanıtları ile optimizasyon | Ölçümsüz üstünlük iddiaları, kritik kalite gerilemesi |
| `0.1.0-beta.7` | Feature freeze, bugfix, stabilizasyon | Açık P0/P1, bozuk migration/recovery |
| `0.1.0-beta.8+` / `1.0.0-rc.n` | Gerektikçe düzeltme ve release candidate | Tüm sürüm kapıları geçilmeden 1.0 etiketi |
| `1.0.0` | İlk kararlı sürüm | Desteklenen platform/agent iddialarının kanıtsız olması |

**Önerilen sürüm numarası semantiği:** beta.2 gibi kullanıcı ifadesi, projenin mevcut şemasıyla `0.1.0-beta.2` / Python `0.1.0b2` biçiminde eşlenebilir; mevcut build sisteminin kanonik biçimini koddan doğrula. Git tag, Python paket sürümü, Tauri package version, installer metadata ve auto-update kanalı aynı sürümün doğrulanabilir karşılıklarını taşımalı. SemVer / PEP 440 dönüşümünü test et.

**Bağımlılık zinciri:** B2 release → B3 desktop/IPC/izinler → B4 bilgi grafı + kaynak modeli + arama + UX → B5 on özellik → B6 tam ölçüm/optimizasyon → B7 freeze → RC → V1.0. Güvenlik, test, dokümantasyon, UX ve migration bütün aşamaları keser.

---

## C. BETA.2 — YAYIN ÖNCESİ MİNİ DOĞRULAMA (YENİDEN GELİŞTİRME DEĞİL)

**Hedef:** Mevcut beta.2 geliştirmesini gerçek yayın paketine dönüştürmeden önce kısa, izlenebilir, veri korumalı kalite kontrolü. `BR-001`–`BR-018` görevlerini tekrar kodlama.

### B2-G00 — Sabitleme ve kanıt dosyası (P0)
- [ ] Yayınlanacak commit'i, branch'i, Git SHA'yı ve yerel çalışma ağacının temizliğini kaydet (`git status --short`, `git rev-parse HEAD`).
- [ ] Bu commit'te mevcut `README`, `docs/ROADMAP.md`, `docs/ROADMAP-EXECUTION.md`, `docs/ARCHITECTURE.md`, `docs/RELEASE-GATE.md`, `PRODUCT_CONTRACT.md`, `COMMANDS.md` dosyalarını kontrol et.
- [ ] Ayrı bir `beta2-release-evidence` JSON/Markdown raporunda platform, Python, paket, mimari, tarih, SHA, test komutu, çıkış kodu, log yolu, manuel adım ve kanıt düzeyi sakla.
- [ ] Hedefler: gerçek kullanıcı verisini testlerde **asla kullanma**; geçici ve ayrı program/veri/kasa/HOME kökleri oluştur.
- **Test:** Kirli git çalışma ağacında yanlışlıkla release üretme engeli; raporda eksik/boş commit reddi.
- **Kabul:** Tam olarak hangi kodun test edildiği ve yayınlandığı belli; kanıt dosyası bulunuyor.

### B2-G01 — Tam test / statik ve bağımlılık denetimi (P0)
- [ ] Repo kökünden mevcut test komutunu çalıştır: `python -m unittest discover -s tests -t .`.
- [ ] `skip`'leri tek tek kategorize et; özellikle platform, semantik sağlayıcı, gerçek API ve gerçek agent testlerini **geçti** diye sayma.
- [ ] Mevcut CI/build/lint/security komutlarını repodan bul ve çalıştır; olmayan komutları uydurma.
- [ ] Paket bağımlılıklarını lisans, güvenlik uyarısı ve sabitlenmiş sürüm açısından denetle; internet gerektiren tarama varsa gerçek kaynak/sonuç tarihini kaydet.
- **Negatif test:** Hata üreten test veya eksik fixture release'i bloke eder.
- **Kabul:** Tüm zorunlu testler `EXIT=0`; skip açıklama tablosu var; P0/P1 açık regresyon yok.

### B2-G02 — Hafıza değerlendirmesini yeniden çalıştır (P0)
- [ ] Mevcut harness ile 50 senaryoyu FTS modunda yeniden çalıştır. Repo belgelerinde kayıtlı komut şablonu: `python -m tests.evals.harness --modes none,fts,hybrid --repeats 3 --json-out <gecici-rapor.json> --md-out <gecici-rapor.md>`; kabul edilen argümanları çalışan sürümden `--help` ile doğrula.
- [ ] Önceki kayıt: FTS %94 / 50 sentetik senaryo; temporal 7/10; update 10/10. Aynı veri seti SHA ve ölçüm koşullarında regressions karşılaştır.
- [ ] `SEMANTIC_OFF`/`unavailable` ise hibrit/semantik için skor uydurma; model gerçekten etkinleştirilmiş ayrı makinede tekrar dene.
- [ ] BR-012 `python -m tests.evals.progressive --json-out <rapor.json> --md-out <rapor.md>` ölçümünü tekrar çalıştır; bütçe, token ve doğruluk karşılaştırması kaydet.
- [ ] Yanlış sonuç kategorilerini (özellikle temporal T01/T02/T07) release notes'a bilinen sınırlama olarak taşı.
- **Kabul:** Aynı fixture'da açıklanamayan regresyon yok; ölçülemeyen kipler eksik olarak etiketlenmiş; sonuç karşılaştırması kayda geçti.

### B2-G03 — Hafıza gerçek yaşam döngüsü smoke (P0)
- [ ] Test kasasında oturum aç → karar yaz → tur/sıkıştırma/kapanış → arka plan flush → günlük → derleme → arama → sonraki oturum context akışını çalıştır.
- [ ] En az bir gerçek Claude Code veya Codex oturumu kullan; gerçek isteğin önemli kararı sonraki farklı agent tarafından bulunabiliyor mu kontrol et.
- [ ] Aynı oturum olayını tekrar göndererek idempotent kayıt; terminali/model çağrısını yarıda keserek güvenli toparlama; iki eşzamanlı writer ile kilit ve atomik işlem testleri yap.
- [ ] Bilinmeyen bilgi sorusunda uydurulmuş cevap yerine belirsizlik; eski karar/yeni karar senaryosunda yalnız güncel kararın öne çıkması.
- **Kabul:** Hiçbir kullanıcı notu zarar görmez, aynı event çift kayıt oluşturmaz; gerçek adapter kullanımının kanıtı sentetik fixture'dan ayrıdır.

### B2-G04 — Agent ve provider matrisi (P0/P1)
- [ ] Claude Code, Codex, Antigravity, Gemini CLI, Cursor, OpenCode için **kurulu / hook doğrulandı / MCP bağlı / gerçek oturum / karşı agent'a geri çağrıldı** alanlarını ayrı raporla.
- [ ] OpenCode için sadece JSONL/eklentinin bağlanması değil, modelin ilgili hafıza bilgisini gerçek istekte kullanması ayrıca test edilsin.
- [ ] OpenRouter için no-key, invalid-key, timeout, ücretli geçiş yasak ve maliyet sınırı testleri; isteğe bağlı gerçek API hesabında en düşük bütçeyle açık izinli smoke yapılabilir. Test gerçekleştirilmediyse `not_real_verified` yaz.
- [ ] Gemini/Cursor yalnız fixture ile testlendiyse tam destek diye reklam yapılmasın.
- **Kabul:** Release notları ve Connections destek rozetleri gerçek test matrisiyle aynı.

### B2-G05 — Mahremiyet, izin, saldırı mini testi (P0)
- [ ] `mcp_write=false` iken yazma aracının görünmediğini ve işlemlerin reddedildiğini test et; izin açıldığında yalnız doğru Inbox'a `pending` kayıt oluşsun.
- [ ] Kasa değişiminde eski MCP oturumunun yeni kasaya veya yanlış kasaya yazamadığını doğrula.
- [ ] Ham arşiv varsayılan kapalı; açık ise maskeli ve saklama süreli; kapatınca yeni arşiv oluşmuyor.
- [ ] Örnek secret/JWT/API key içeren senaryo, kötü niyetli README ve prompt injection metniyle özetleme/geri çağırma testlerini çalıştır.
- [ ] OpenRouter anahtarı, oturum ham metni veya özel dosya içeriği log/hata/telemetriye düşmesin.
- **Kabul:** P0 veri sızıntısı, izinsiz yazma veya yetkisiz kullanıcı kuralı yükseltmesi yok.

### B2-G06 — Frozen build, kurulum, yükseltme, kaldırma (P0)
- [ ] Repo belgesinde geçen Windows dağıtım komutunu doğrula ve çalıştır: `python packaging/build_dist.py --platform windows --output dist`.
- [ ] Dağıtım bütünlüğü: `python -m unittest tests.packaging.test_distribution -v`; migration: `python -m unittest tests.installation.test_migrate -v`.
- [ ] Önce beta.1 gerçek fixture'ından beta.2'ye yükseltme ve eski notları bayt karşılaştırması; temiz kurulum, onarım, kaldırma, yeniden kurulum, kasanın korunması ve yanlış/eksik paket durumlarında geri alma.
- [ ] Aynı HOME'da başkasının oluşturduğu agent ayarları korunmalı; Brain yalnız kendi manifest girdisini değiştirmeli.
- [ ] Windows 11 x64 geçici gerçek kurulum smoke ve paket hash/SHA-256 kaydı.
- [ ] Authenticode yoksa açık olarak `UNSIGNED` göster; SmartScreen uyarısı ihtimalini yayın notuna ekle; imzalı yayın iddia etme.
- **Kabul:** Kasa, state, üçüncü taraf ayarlar ve kurulum manifest'i hatasız korunur; paket ve rollback testleri kanıtlı.

### B2-G07 — Dokümanları eşitle ve beta.2 yayın kararı (P0)
- [ ] `ROADMAP.md` içinde artık uygulanmış OpenRouter/OpenCode/indeks gibi konuların eski metinlerini **silmeden önce** `ROADMAP-EXECUTION.md` kanıtlarıyla eşleştir; ürünün izleme sözleşmesine göre tamamlanan açık boşlukları kapat ve kalan gerçek doğrulamaları yeni görev olarak bırak.
- [ ] `RELEASE-GATE.md` beta.1 geçmişini koru; beta.2 için yeni tarih/commit/fixture/test/kanıt düzeyi olan bölüm veya sürümlü rapor ekle.
- [ ] Git tag, Windows setup/exe, checksum, changelog, destek/deneysellik, known issues ve kurulum geri alma talimatlarını üret.
- [ ] Son kullanıcıya veri aktarımı, bulut sağlayıcısı ücretlendirmesi ve ham sohbet arşivi varsayılanları açık anlatılır.
- **Kabul:** Yayın kontrolü PASS ise beta.2 çıkabilir; FAIL ise ilgili issue açılır, beta.2 etiketi atılmaz.

**Beta.2 mini doğrulama pratik sırası:** G00 → G01 → G02 → G03 → G04 → G05 → G06 → G07. Bu kontrol yeni bir büyük geliştirme sprinti değildir; bulunan P0/P1 hata hemen giderilir.

---

## D. BETA.3 — BAĞIMSIZ TAURI 2 + REACT + TYPESCRIPT BRAIN APP, PYTHON CORE

### D.0. Nihai ürün deneyimi

Kullanıcı yalnız Brain'i kurup kullanabilmeli. Arayüz Hub'ı gerektirmemeli. Gerekli ekranlar: **Overview/Dashboard, Memory Explorer, Search & Recall, Timeline, Review Center, Connections, Sources/Imports, Settings/Privacy/Providers, Health/Diagnostics, Backup/Recovery**. Beta.4–5 modülleri için yan menü/bilgi mimarisi genişletilebilir olmalı.

### D.1. Temel mimari kararlar (ADR olarak kaydet)

1. UI: **Tauri 2 / React / TypeScript**; Rust yalnız Tauri barındırıcısı ve dar OS entegrasyonu. Hafıza/özetleme/search/RPP implementasyonu **Python**.
2. Sidecar: Python çekirdek paketini mevcut frozen dağıtım yaklaşımıyla Tauri `externalBin` veya belgelenmiş eşdeğer yöntemle paketle. Sidecar güncelleme/kill/zombi/port-kapışma/çökme davranışları açıkça tasarlanmalı.
3. UI ↔ Python protokolü: JSON şemalı **sürümlü** ve idempotent yetkili IPC. Prototipte stdio request-response makul bir ilk seçenektir; HTTP localhost seçilirse rastgele port, token/OS erişim sınırı, origin ve CSRF/host koruması açıkça tasarlanır. Nihai taşıma yöntemini benchmark/ADR ile seç.
4. UI asla kasa Markdown'ına veya SQLite indekse kontrolsüz doğrudan yazmaz; mutasyon Python domain servisinden geçer.
5. Tek *source of truth*: `settings.py`, vault UUID, veri kökü, provenance ve izin sistemi. TypeScript tarafındaki tipler Python şemalarından üretilir veya contract testleriyle eşlenir.
6. Çekirdek **headless** çalışır. Tauri kapatılınca Python sidecar GUI oturumunun ilgili süreci kapanabilir ama agent CLI/MCP/RPP bağımsız başlatılıp çalışabilir. 'Tray' ile kapanma ve tam kapatma açıkça ayrılır.
7. Varsayılan olarak hiçbir ağ telemetrisi ve ücretli model kullanımına geçiş yok; dış bağlantı için açık onay ve data-egress denetimi.
8. Hub'dan taşınmada **kasa UUID korunur**, notlar kopyalanıp çatal oluşturulmaz; eski sistemle birlikte çalışmada sahiplik ve uninstall sınırları korunur.
9. Temalar/tasarımlar platformlar arasında ortak olabilir, ama ürün dosyalarının, kullanıcı izinlerinin ve kurulumun sahibi yalnız Brain'dir.
10. Gerçek OS desteği beta.2'nin Windows x64 düzeyinden otomatik yükseltilmez; macOS/Linux hedefleri ayrı build/test kapısı ister.

### D.2. UI'nin gelecekte büyümesi için sabit modüller

- `shell/`: navigation, pencere, theme, locale, crash boundary, klavye kısayolları.
- `features/overview`: sağlık, durum, son işlemler.
- `features/memories`: bütün hafızalar, detay, ilişkiler, kaynak durumları.
- `features/retrieval`: arama, filtre, context preview, token bütçesi.
- `features/review`: inbox, onay/red/düzeltme, çelişki.
- `features/timeline`: gün/oturum/agent/karar geçmişi.
- `features/connections`: provider ve agent kurulum, izin ve test.
- `features/sources`: dosya, URL, eski konuşma içe alma; orijinal kaynak önizleme.
- `features/settings`: kasa, model, API anahtarları, gizlilik, export/import, yedek.
- `features/diagnostics`: hata, pipeline durumu, güvenli destek paketi.
- Beta.4 eklentileri: Graph, Knowledge Maintenance, Skills/Hand-off temel navigasyon hazırlığı.
- Beta.5 eklentileri: Time Machine, Evidence Chain, Conflict Resolver, Privacy Firewall, Replay/Simulator, Impact Advisor, Freshness Guardian, Quality Observatory, Skills Lab.

### D.3. Beta.3 uygulanabilir görevler

#### B3-001 — Repo ve bağımsızlık denetimi (P0, S)
- **Bağımlılık:** B2-G07.
- **Mimari:** Hub'a doğrudan UI/installer/RPP çağrısı bağımlılıklarını çıkar; Brain'in kurulum, erişim, update, health, kasa, uninstall işlerini hangi modülün sahiplenmesi gerektiğini ADR'ye bağla.
- **İşler:** [ ] Tüm kullanıcı giriş noktalarını listele. [ ] Hub çağrısı zorunlu olanları ayır. [ ] Brain'e özgü data ve OS kayıtlarını sahiplik envanterine geçir. [ ] Eski Hub'da açık kalan kısayol/ayarları yanlışlıkla silmeden geçiş stratejisi yaz.
- **Test:** Hub kurulu değilken CLI/MCP/search/backup smoke; Hub varken eşzamanlı kullanım.
- **Kabul:** Brain'in çalışması için gereken sıfır zorunlu Hub çağrısı; geçişte hangi bileşenin kime ait olduğu kayıtlı.

#### B3-002 — Tauri shell ve React tasarım altyapısı (P0, M)
- **Bağımlılık:** B3-001.
- **İşler:** [ ] Tauri 2 workspace, React/TS ve route iskeleti. [ ] Tasarım tokenları (renk, tipografi, aralık, radius, ikon, durumlar). [ ] Koyu/açık tema, reduced-motion, ekran ölçekleme. [ ] ESLint/TS strict ve bileşen test altyapısı. [ ] Windows imza/manifest/build hedefi.
- **Test:** Unit ve component smoke; network erişimi gerektirmeyen boş uygulama açılışı; %100/125%/150% DPI.
- **Kabul:** Tek installer ile açılan, erişilebilir ve responsive bağımsız Brain shell; Hub olmadan açılıyor.

#### B3-003 — Python sidecar paketleme ve yaşam döngüsü (P0, L)
- **Bağımlılık:** B3-002; mevcut `packaging/build_dist.py` altyapısı.
- **İşler:** [ ] Python motorunun yeni UI ile paketlenme biçimini seç. [ ] `externalBin`/sidecar çift sürüm uyumunu kontrol et. [ ] Process spawn/stop, stdout/stderr protokolü, restart, crash recovery, timeout, zombie cleanup. [ ] İki pencere/uygulama örneğinde çift writer engeli. [ ] Antivirüs/SmartScreen/signed binary etkisi.
- **Test:** Yanlış sidecar path, çökme, 10x başlat/kapat, açık GUI olmadan CLI/MCP, yarım kalan update, boşluk/Unicode içeren Windows path.
- **Kabul:** Python kurulu olmayan makinede Brain UI ve core çalışıyor; GUI kapalıyken CLI/MCP bozulmuyor; paket açılışından kapanışa süreç sızıntısı yok.

#### B3-004 — Sürümlü IPC + yetki modeli (P0, L)
- **Bağımlılık:** B3-003.
- **İşler:** [ ] `protocol_version`, `request_id`, `vault_uuid`, `result`, `error_code`, `capabilities` alanlarını tanımla. [ ] Okuma ve mutasyon işlemlerini ayır. [ ] Her mutasyon için etkili vault/permission kontrolü. [ ] Şema doğrulama, payload boyut ve zaman sınırları. [ ] TS/Python contract testi, backward compatibility. [ ] IPC log redaction ve hata ayrıştırma.
- **Test:** Eski UI↔yeni core, yeni UI↔eski core; bozuk JSON, bilinmeyen komut, yanlış kasa UUID, yetki kapalı yazma, birden fazla eşzamanlı istek.
- **Kabul:** Yetkisiz istek fail-closed; farklı protokol sürümleri anlaşılır mesaj verir; UI doğrudan dosya yazarak izni bypass edemez.

#### B3-005 — Kasa ve kurulum taşınması (P0, L)
- **Bağımlılık:** B3-001, B3-004.
- **İşler:** [ ] Beta.2 kurulum/kasa UUID/ayar/state'i keşfet. [ ] Önizleme: tutulacak dosya, değişecek kayıt, rollback. [ ] Eski veri kökünü koruyarak yeni UI bağlantısını kur. [ ] Manifest ve kısayol sahipliği, karşı uygulama ayarlarını koruma. [ ] Migration journal, backup, recovery. [ ] Eski kurulumla eşzamanlı erişimde kasa kilidi.
- **Test:** Temiz beta.3; beta.2→beta.3; beta.1→beta.3 desteklenen geçiş yolu; kasası USB'de; OneDrive/redirected Documents; uzun Unicode path; çift vault; downgrade denemesi.
- **Kabul:** Kullanıcı notları bayt düzeyinde korunur; UUID değişmez; rollback mümkün; Hub/Orchestrator dosyaları Brain uninstall'ından etkilenmez.

#### B3-006 — Onboarding ve bağlantı sihirbazı (P0, M)
- **Bağımlılık:** B3-004/005.
- **İşler:** [ ] İlk açılış: eski kasayı bul veya yeni kasa seç. [ ] AI araçlarını tespit et; gerçekte var olmayan istemciyi kurulu gösterme. [ ] Hook/MCP izin adımları, kurulum önizleme, onay ve geri al. [ ] Demo/test kasa seçeneği, ilk hafıza testi. [ ] Bilgilendirme: API vs CLI, ham döküm saklama, maliyet, offline davranış.
- **Test:** Onboard iptali, program admin olmayan kullanıcı, bozuk config, sıfır agent kurulu, geçersiz kasa yolu.
- **Kabul:** Yeni kullanıcı Hub bilmeden Brain'i kurar, kasasını seçer ve ilk aramayı gerçekleştirir; istemci onayı yoksa açıkça görünür.

#### B3-007 — Dashboard ve sağlık görünümü (P0, M)
- **Bağımlılık:** B3-004.
- **İşler:** [ ] Mevcut `health` JSON'dan sadece güvenli gösterilebilir alanları kullan. [ ] Son capture/flush/index/scheduler durumu, agent bağlantıları, pending review. [ ] Sorun → teşhis → kullanıcı onaylı repair akışı. [ ] Son etkinlikleri ham sohbet metni olmadan özetle.
- **Test:** Kasa yok, izin reddi, provider kota doldu, indeks eski, hook reddi; parola/oturum yolu sızması testi.
- **Kabul:** Hangi modülün çalışmadığı kullanıcı tarafından anlaşılabilir; gizli içerik Dashboard'a sızmaz.

#### B3-008 — Memory Explorer ve not detayları (P0, L)
- **Bağımlılık:** B3-004.
- **İşler:** [ ] Kasa/proje/tür/agent/güncellik filtreleri. [ ] Kaynak, güven, doğrulama, karar yaşam döngüsü göstergesi. [ ] Markdown önizleme; açık izin varsa kontrollü düzenleme. [ ] Not ilişkileri, Obsidian'da aç, dosya yolunu gör. [ ] Null/yanlış/bozuk frontmatter durumu.
- **Test:** 10k notlu sentetik kasa, symlink/kasa dışı not, iki agent aynı notu güncelliyor, çözümlenemeyen kaynak.
- **Kabul:** Notlar dosya kaynağıyla eşleşir; değişiklik atomic/hash kontrollüdür; indirilmiş/harici not gizlice değişmez.

#### B3-009 — Search & Recall Explorer (P0, M)
- **Bağımlılık:** B3-004; mevcut BR-011/012.
- **İşler:** [ ] FTS/semantik/hibrit modları; seçili mode unavailable ise dürüst durum. [ ] Kaynak yol, bölüm/özet, güven, alaka işareti. [ ] Token bütçesiyle context önizleme; tam nota geçiş. [ ] Kaynak/doğruluk ve sonuç filtresi; copy/export. [ ] `Recall` sadece ilgili hafızayı gösterir, bütün vault'u prompt'a eklemez.
- **Test:** Eski karar/yenisi, unicode Türkçe, boş sorgu, büyük not, semantik off, düşük alaka, yetkisiz projeyi sonuçlara katmama.
- **Kabul:** Arayüzde görülen ilk sonuç ile MCP'nin aynı sorgu/ayar altında seçtiği sonuç eşleşir; izin filtreleri bypass edilemez.

#### B3-010 — Timeline + oturum geçmişi (P1, M)
- **Bağımlılık:** B3-004.
- **İşler:** [ ] Oturum, günlük, kaynak, karar, ajan ve olay kronolojisi. [ ] Ham transcript kapalıysa bunu açıkça göster; boş kayıttan sahte ayrıntı üretme. [ ] Timeline olayına kaynak bağlantısı. [ ] Gün/tarih aralığı ve proje filtreleri.
- **Test:** Saat dilimi farkı, saat geri alma, kaynak kayıp, arşiv retention dolması.
- **Kabul:** Zaman alanlarının anlamı ayrılır; kaynağı olmayan olay doğrulanmış içerik gibi görünmez.

#### B3-011 — Review Center (P0, L)
- **Bağımlılık:** B3-004; mevcut BR-009.
- **İşler:** [ ] Inbox, bekleyen öğrenim, önerilen karar, çelişki ayrı filtreler. [ ] Kabul/reddet/düzelt/erteleyip not ekle. [ ] Geri alma/diff, kaynak incele, yetkili kullanıcı eylem kaydı. [ ] Onay sonrası atomik kayıt ve index invalidation.
- **Test:** Çift tıklama, eşzamanlı değişiklik, yetki geri alma, reddedilen önerinin tekrar gelmesi, modelin `verified` olmaya çalışması.
- **Kabul:** Kullanıcı onayı olmadan kalıcı kural yükselmiyor; inceleme kararları kayda geçiriliyor ve geri alınabiliyor.

#### B3-012 — Connections ve provider yönetimi (P0, L)
- **Bağımlılık:** B3-004/006.
- **İşler:** [ ] Claude, Codex, Antigravity, Gemini, Cursor, OpenCode status matrisi. [ ] Hook kurulumu, onay ve izin kaldırma; MCP araç listesi. [ ] Model/sağlayıcı/ücretli kullanım ayarı; API key UI'da maskeli, kopyalanmaz. [ ] Özetleyici deneme, 10 tokenlik smoke değil gerçek destek göstergesi. [ ] Kurulum dosyalarını değiştirmeden önce diff/owner göster.
- **Test:** Ücretli sağlayıcıya yanlışlıkla geçiş, yanlış context, bağlantı kaybolması, değişen agent CLI sürümü.
- **Kabul:** 'Kurulu' ile 'gerçek uçtan uca doğrulanmış' ayrıdır; secret UI/frontend loglarına düşmez.

#### B3-013 — Backup / Restore / Settings / Privacy (P0, L)
- **Bağımlılık:** B3-004/005.
- **İşler:** [ ] Mevcut restic/Git yedeklerini UI'da onaylı akışla sun. [ ] Restore önizleme, yeni klasöre geri alma, yanlış kasaya üzerine yazmayı engelle. [ ] `archive_transcripts`, retention, data-egress, provider izinleri, manuel capture seçimi. [ ] Yedek şifreleri ve credential alanları güvenli.
- **Test:** Yedek bozuk, disk dolu, yedek sırasında aktif writer, geri yüklemede UUID çatışması, eski backup dosyası.
- **Kabul:** Backup doğrulanabilir; restore varsayılan olarak mevcut kasayı ezmez; kullanıcı etkisi net.

#### B3-014 — UI performans, erişilebilirlik, tasarım kalite kapısı (P1, M)
- **Bağımlılık:** B3-002 ve ekranlar.
- **İşler:** [ ] İskelet/boş/hata/yükleniyor durumları; büyük listede sanallaştırma. [ ] Klavye, ekran okuyucu etiketleri, kontrast, focus ve reduced-motion. [ ] Bileşen görsel regresyonları. [ ] İlk açılış, RAM/CPU, filtre/arama gecikmesi ölçümleri.
- **Araç referansları:** [Vercel Agent Skills](https://github.com/vercel-labs/agent-skills), [AI Design Check](https://github.com/enmerasoftware/ai-design-check), [Unslop](https://github.com/heydamir/unslop); araçların raporu insan tasarım incelemesinin yerine geçmez.
- **Kabul:** Kritik ekranlar erişilebilir; ölçülmüş performans raporu var; dekoratif animasyonlar işlevi engellemiyor.

#### B3-015 — Tauri release, bağımsızlık ve OS smoke (P0, L)
- **Bağımlılık:** B3-001…014.
- **İşler:** [ ] Paket sürüm eşleme, sidecar hash, updater imza, dağıtım kaynağı ve manifest. [ ] Windows temiz kurulum ve beta.2 yükseltme. [ ] CLI/MCP GUI kapalı testleri. [ ] Package signing durumu, SmartScreen bilgi metni. [ ] macOS/Linux ancak gerçek runner/build/test varsa destek ilanı.
- **Test:** UI crash, sidecar crash, uygulama kapalı agent isteği, geçersiz updater, uninstall ve yeniden kurulum, offline güncelleme.
- **Kabul:** B3 Release Gate kayıtlı; Hub olmadan tüm çekirdek akışlar başarılı; kullanıcı verisine zarar yok.

### D.4. Beta.3 yayın çıkışı ve beta.4 hazırlığı
- [ ] Beta.3 tasarımının **gelecekteki 10 beta.5 ekranına** yer açtığını IA/route review ile doğrula; ekranların hepsini beta.3'te uygulama zorunluluğu yok.
- [ ] Beta.4 için graph/index/review/source/permission domain API'lerinin sürümlü genişleme noktalarını tanımla.
- [ ] Beta.3 bittikten sonra sidecar'ın Python→Rust taşınması otomatik başlamaz; performans/taşıma maliyeti gerçek ölçümle ayrıca değerlendirilir.
- [ ] Beta.2'den beta.3'e geçen en az 3 farklı fixture: boş kasa, çok notlu kasa, çoklu agent/kasa.
- [ ] Beta.3'e geçerken mevcut `BR-*` yürütme kayıtları tarihçesi korunur.

---

## E. BETA.4 — KAPSAMLI RAKİP EŞİTLİĞİ VE HAFIZA YETENEKLERİ

### E.0. Kapsamın doğru tanımı

Ürün sahibi, rakiplerin **tüm özelliklerini** inceleme ve Brain'in uygun tüm yetenekleriyle daha iyi hale gelme hedefini onayladı. Bu nedenle:

1. Hiçbir rakip özelliği sessizce atlanmaz; her biri kayıt edilir.
2. Bir özelliğin *rakipte belgelenmesi* ile bağımsız olarak doğrulanmış olması ayrılır.
3. Brain'in temel işiyle ilişkili **hafıza yetenekleri** Beta.4 parity kapsamına alınır.
4. Takvim, CRM, IDE, agent yürütmesi, tam kod analizi, podcast üretimi vb. komşu alanlar incelemede tutulur; Brain'e birebir gömmek zorunda değiliz. Bağlayıcı / Orchestrator / Hub / kapsam dışı kararı yazılır. Kullanıcı bunu 'atlanmış özellik' sanmamalı.
5. Feature parity yalnız aynı isimli buton değildir; davranış + güvenlik + veri bütünlüğü + UX + test eşitliği anlamına gelir.
6. **Dondurulmuş rakip kesiti:** 2026-11-05 başlangıç görüntüsü; beta.4 başında resmi `snapshot_date`, repo commit/tag, lisans ve README URL'si alınır. Daha sonra gelen rakip yenilikleri ayrı `delta` havuzuna eklenir; scope creep sürümü sonsuzlaştırmaz.
7. Beta.4'te bazı temel özellikler beta.2'de var olabilir; `EXISTING-VERIFY` ile işaretleyip sadece farkı geliştir.

### E.1. Rakip kayıt formatı (COMPETITOR REGISTRY)

Her rakip için zorunlu alanlar:
- `competitor_id`, ürün adı, repo URL'si, homepage/doc URL, görüntülenen commit/tag ve kaynak görüntüleme tarihi.
- Lisans ve üçüncü taraf bağımlılıklar; bakım durumu, desteklenen agent/OS, kurulum biçimi.
- **TÜM tespit edilen özellikler**: kısa açıklama, kullanıcı sonucu, varsayılan/opsiyonel, izin/ücret/bağımlılık, somut kanıt URL/dosya/başlık/commit.
- Aynı özelliğin rakipler arası ortak bir `capability_id` altında birleştirilmesi; tek bir özellik 10 rakipte varsa 10 ayrı uygulama yazma.
- `brain_state`: `existing`, `partial`, `missing`, `unverified`.
- `decision`: `native-core`, `native-desktop`, `optional-adapter`, `orchestrator-contract`, `hub-contract`, `out-of-scope-explicit`.
- `why`, `owner`, `target_beta`, `dependencies`, `security_assessment`, `UX_flow`, `test_case_ids`, `acceptance`, `evidence`, `implementation_commit`, `verification_status`.
- `better_than_competitor_hypothesis`: nerede daha iyi olacağız? **Hipotez**, ölçülmeden gerçek iddiası sayılmaz.
- Parity kanıtı: rakibin aynı görevi nasıl yaptığı (docs/demo/test) ile Brain'in aynı görevi nasıl yaptığı (fixture/test/gerçek oturum).

### E.2. Zorunlu rakip tarama listesi — önceki 13 + yeni 4, en az 17

| ID | Rakip | Kaynak | Temel karşılaştırma grubu |
|---|---|---|---|
| C01 | Avenox Beyin | https://github.com/avenoxai/avenoxbeyin | Markdown, çoklu agent, seçici öğrenim, hızlı yakalama, bağlam kontrolü |
| C02 | Hafıza OS | https://github.com/fornhere/hafiza-os | Kaynak/doğrulama, karar, devam kapsülü, kavram sentezi |
| C03 | Obsidian Mind | https://github.com/breferrari/obsidian-mind | Vault düzeni, çalışma bağlamı, kişi/proje, düzeltme, güven düzeyi |
| C04 | Obsidian Second Brain | https://github.com/eugeniughelbur/obsidian-second-brain | Skill/komutlar, Crew, research, görev, tekrar, bilgi bakımı |
| C05 | Obsidian Wiki | https://github.com/Ar9av/obsidian-wiki | Geçmiş içe alma, arama, wiki bakımı, graph/backup/export/skill üretimi |
| C06 | Claude-Mem | https://github.com/thedotmack/claude-mem | Otomatik gözlem, context, UI, seçici arama, hosted opsiyonlar |
| C07 | MemPalace | https://github.com/MemPalace/mempalace | Raw kaynak, zamanlı KG, çoklu-agent olaylar, tasks, artefaktlar |
| C08 | Claude Obsidian | https://github.com/AgriciDaniel/claude-obsidian | Kaynaklardan wiki, yazma onayı, provenance, not grafı |
| C09 | Context Mode | https://github.com/mksglu/context-mode | Tool output izolasyonu, token/context verimi, retrieval |
| C10 | Everything Claude Code | https://github.com/affaan-m/ECC | Memory Vault, öğrenilmiş alışkanlık/skill, agent kuralları |
| C11 | Codebase Memory MCP | https://github.com/DeusData/codebase-memory-mcp | Kalıcı kod grafı, etki analizi, kod ile hafıza bağlantısı |
| C12 | Graphify | https://github.com/Graphify-Labs/graphify | Kod/bağımlılık ilişkileri, kaynak kanıtlı graph, görselleştirme |
| C13 | Open Notebook | https://github.com/lfnovo/open-notebook | PDF/web/ses/video kaynakları, notebook, kaynaklı araştırma |
| C14 | Hindsight | https://github.com/vectorize-io/hindsight | Fact/belief, retain/recall/reflect, temporal/graph/hybrid |
| C15 | Supermemory | https://github.com/supermemoryai/supermemory | Profil, güncellenen bilgiler, kaynak entegrasyonları |
| C16 | Cognee | https://github.com/topoteretes/cognee | Kaynaklardan bilgi grafı ve semantik hafıza |
| C17 | MemOS | https://github.com/MemTensor/MemOS | Çok katmanlı hafıza, öğrenim, skill reuse, maliyet |

**Zorunlu geniş rakip taraması:** Mem0 (`https://github.com/mem0ai/mem0`), Letta (`https://github.com/letta-ai/letta`), Zep/Graphiti (`https://github.com/getzep/graphiti`), yeni agent memory ürünleri ve yayınlar. Bu üç ürün minimum araştırma setine eklenir; yeni rakip bulunduğunda `C18+` ile kayıt açılır. **Hiçbir rakip için 'tamamen eksiksiz incelendi' demek yalnız README okumakla mümkün değildir:** docs, changelog, test, source, config, CLI, UI ve release notes kontrol edilir.

### E.3. 135 araçlık kataloğun kaybolmaması gereken rolü

Kullanıcı tarafından sağlanan `ai_coding_135_kategorili_rehber.html` (2 Kasım 2026; **135 kayıt, 16 kategori**) bu çalışmaya girdi oluşturdu. Geçici `docs/kaynak` silinmeden önce, ilgili *Brain* kayıtlarının açık adları/URL'leri ve kararları bu belgeye işlendi. Katalog tümüyle Brain rakip listesi değildir; UI tasarım, güvenlik ve destek araçları da bulunur. Beta.4 keşfinde kataloğun tamamını tekrar sınıflandırıp [kapsam dışı / iş ortağı / güvenlik / UX / rakip] durumlarını ayrı registry'de belgeleyin. `ai_coding_135_kategorili_rehber.html` silindikten sonra yeni geliştirici için en azından bu bölümdeki repo URL'leri ve aşağıdaki çapraz-kategori adayları kalacaktır.

- `#011 Avenox`, `#045 Hafıza OS`, `#068 Obsidian Mind`, `#069 Obsidian Second Brain`, `#070 Obsidian Wiki`, `#095 Claude-Mem`, `#057 MemPalace`: birincil doğrudan rakipler.
- `#022 Claude Obsidian`, `#054 Open Notebook`, `#061 Context Mode`, `#034 ECC`, `#030 Codebase Memory MCP`, `#043 Graphify`: yakın/kısmi rakipler.
- `#042 Graft` https://github.com/trailhq/Graft; `#047 Headroom` https://github.com/headroomlabs-ai/headroom; `#059 Semble` https://github.com/MinishLab/semble; `#076 Serena` https://github.com/oraios/serena: bağlam/kod arama **entegrasyon araştırmaları**, varsayılan olarak Brain çekirdeği değil.
- `#092 Task Observer` https://github.com/jonbobo212/task-observer; `#090 Superpowers` https://github.com/obra/superpowers; `#089 Spec Kit` https://github.com/github/spec-kit: öğrenim/skill ve süreç referansı.
- `#023 Cloudflare Security Audit Skill` https://github.com/cloudflare/security-audit-skill; `#134 AI Design Check` https://github.com/enmerasoftware/ai-design-check; `#133 Unslop` https://github.com/heydamir/unslop; `#102 Vercel Web Design Guidelines` https://github.com/vercel-labs/agent-skills/tree/main/skills/web-design-guidelines: kalite denetimi adayı.
- `#132 MangoDisk` https://github.com/harry0703/MangoDisk: Tauri masaüstü UX/paketleme tasarım referansı, **Brain rakibi değil**.
- `#128 DeepSeek DSH` https://github.com/deepseek-ai/dsh-superagent-prototype, `#131 Open Space` https://github.com/Fantomiald/open-space: oturum koordinasyonu/agent gözlemi referansı; görev yürütme Orchestrator sorumluluğunda.

### E.4. Tam özellik envanterinde unutulmaması gereken kategori ve alt maddeler

Aşağıdaki yetenekler registry'de **ayrı capability ID** almalı; hepsi tek satır 'memory features' haline getirilmemeli:

1. **Capture:** Oturum başı/tur/araç kullanımı/sıkıştırma/kapanış, seçici/manual capture, olay kaybı/kurtarma, idempotency, import legacy, dış kaynak alma, redaction, günlük/sabah özeti.
2. **Memory primitives:** Kullanıcı tercihi, talimat, olgu, gözlem, deneyim, inanç/yorum, hata, çözüm, karar/ADR, açık iş, proje özeti, kişi/ekip, kod bağlamı, kaynak, transkript.
3. **Provenance/trust:** Source SHA/URI/agent/session/time, verified/inferred/unverified/rejected, güven skoru, kullanıcı onayı, orijinal kaynak koruma, hash/diff, audit trail.
4. **Temporal:** `observed_at`, `recorded_at`, `valid_from`, `valid_until`, `supersedes`, geçmişte geçerli karar, yeni bilgiyle eskiyi iptal, timeline ve change diff.
5. **Knowledge graph:** Kavram, kişi/proje/agent/oturum/karar düğümleri, typed ilişkiler, graph traversal, orphan/duplicate/contradiction, görsel graph, source evidence, export.
6. **Retrieval:** FTS, embeddings, hybrid, reranking, MRR/Recall, query expansion, time filtering, intent/project scope, multi-step short→summary→full, negative queries, context pack, explainability.
7. **Context:** Başlangıç özeti, aktif konu, hedefler, budget, token savings, kaynaklı context, stale/secret exclusion, no-irrelevant-injection, work continuity.
8. **Agent integration:** Claude Code/Codex/Antigravity/Gemini/Cursor/OpenCode ve geçerli başkaları, MCP, hooks, CLI, plugin, provider choice, API, permission, active session.
9. **Collaboration:** Kimin ne öğrendiği, agent günlüğü, iş devri, handoff evidence, artifact id/hash, approval; **agent scheduling/execution Orchestrator'a gider**.
10. **Source ingestion:** Markdown, TXT, kod, PDF, HTML/URL, docs, ses/video transcript (opsiyonel parser), repo, browser capture; SSRF/secret/permission ve lisans.
11. **Vault operations:** Vault health, dedup, merge, archive, broken links, review queue, taxonomy, Obsidian graph/Bases/Canvas uyumu, tags, search reindex, migration.
12. **I/O/Portability:** Markdown/JSON, kaynak provenance manifest'i, export/import, Obsidian uyumu, backup/restore, opsiyonel graph export, portability testleri.
13. **Security:** secret redaction, injection, memory poisoning, permission revocation, scope isolation, local-first, offline mode, data egress, provider billing, audit privacy, retention/purge.
14. **UX:** Desktop dashboard, Memory Explorer, source chain, search explain, Review, Timeline, connections, diagnostics, diff, graph, keyboard/accessibility.
15. **Learning:** Yeni öğrenim adayları, hatalardan kural çıkarımı, onay, skill taslağı, skill testleri, kullanıldığı bağlam/başarı kanıtı, geri alma.
16. **Research/work:** Çoklu kaynak sentezi, kaynaklı araştırma, bilgi güncelleme; doğrudan genel tarayıcı automation ve personal CRM kapsama kararı ile ayrılır.
17. **Operations:** Kurulum, repair, recovery, kill/restart, token/cost/latency metrikleri, şema ve index rebuild, release/update/imzalama.

### E.5. Beta.4 geliştirme paketleri ve görevler (B4-001…B4-025)

#### B4-001 — Rakip özellik registry'si ve 17+ rakibin yeniden doğrulanması (P0, L)
- **Bağımlılık:** B3-015.
- **İşler:** [ ] E.1 kayıt şemasını oluştur. [ ] C01–C17 her biri için README, docs, kaynak kod, CLI, test, release notes incelensin. [ ] Mem0, Letta, Graphiti ve yeni rakipler eklenir. [ ] Özellikler `capability_id` ile tekilleştirilir. [ ] Kapsam belirsizliğinde `UNVERIFIED` bırak. [ ] Her özelliğe Brain'deki karşılık ve mimari karar ekle.
- **Test:** Registry validator: URL, kaynak, tarih, durum, karar, owner, acceptance alanları eksik kaydı reddeder; yinelenen capability kaybı testi.
- **Kabul:** Her rakip için kaynaklı yetenek kataloğu; hiçbir özellik isimsiz/gerekçesiz yok; rakip snapshot commit/tarih kaydı mevcut.

#### B4-002 — Parity ve kapsam kararı incelemesi (P0, M)
- **Bağımlılık:** B4-001.
- **İşler:** [ ] `native-core`, `desktop`, `adapter`, `orchestrator`, `hub`, `explicit-out-of-scope` matrisi. [ ] Her `native` kabiliyet için iş paketi ve owner. [ ] Reddedilen/harici özelliklere kullanıcı etkisi ve gerekçe. [ ] Tüm hedefler arasında bağımlılık sıralaması. [ ] Ürün sahibi onaylı frozen scope.
- **Test:** 100% registry entry karar/owner/test association. İlgili capability 2 projeye veriliyorsa arayüz protokolü tanımlı.
- **Kabul:** 'Rakipte var fakat bizde hiç değerlendirilmedi' sayısı **0**. Hedef hafıza kabiliyetleri `PLANNED`/`EXISTING-VERIFY` olarak gösteriliyor.

#### B4-003 — Kanonik memory entity ve provenance tasarım incelemesi (P0, L)
- **Bağımlılık:** B4-002; BR-007/008.
- **İşler:** [ ] Mevcut frontmatter ve Markdown biçimini doğrula. [ ] Olgu, gözlem, deneyim, yorum, tercih, kural, karar için canonical type. [ ] Kaynak/validity/confidence/approval ilişkileri. [ ] Kaynağı kaybolan notta bozuk link yerine `source_unavailable`. [ ] Şema sürümü/migration/backfill stratejisi.
- **Test:** Bozuk metadata, manuel Obsidian düzenlemesi, eski not, kayıp kaynak ve yanlış SHA. Doğrulanmamış eski notların otomatik verified olmaması.
- **Kabul:** Her kritik memory kaydında `what/how/when/by whom/from where` izlenebilir; eski kasa korunur.

#### B4-004 — Derived Temporal Knowledge Graph (P0, XL)
- **Bağımlılık:** B4-003.
- **İşler:** [ ] Not, karar, proje, kişi, agent, oturum, kaynak düğümleri; `references`, `contradicts`, `supersedes`, `caused_by`, `derived_from`, `related_to` typed edges. [ ] `recorded_at` vs `valid_from` vs `valid_until`. [ ] Kaynak URL/hash ve provenance. [ ] Graph'ı Markdown/metadata'dan rebuild edilebilir indeks olarak tut; yeni zorunlu server kurma. [ ] Incremental invalidation, checksum, graph traversal, bulk rebuild.
- **Test:** Aynı düğümün yeniden indekslenmesi, yanlış/cycle edge, stale temporal, kayıp belge, 10k düğüm/100k kenar sentetik yük, graph rebuild sonrası eşdeğerlik.
- **Kabul:** 'Geçen hafta hangi karar geçerliydi?' kaynaklarıyla cevaplanır; graph cache silinse Markdown'dan aynı ilişki grafı üretilir.

#### B4-005 — Source Trust, Fact/Inference/Opinion ayrımı (P0, L)
- **Bağımlılık:** B4-003/004.
- **İşler:** [ ] Hindsight benzeri world/experience/observation/opinion ayrımını birebir kopyalamadan veri türü/sinyal katmanı olarak uygula. [ ] İnsan onaylı bilgi, model çıkarımı, üçüncü taraf belge, otomatik çıkarılmış kod gerçeği ayrımı. [ ] Kaynak hash değişirse güven statüsünü güncelle. [ ] Kullanıcıya açıklanabilir source status.
- **Test:** İki çelişkili kaynak; model görüşünün kullanıcı onaylı gerçeği ezmemesi; kaynağı değişen bilgi; hâlihazırda onaylı notu bozma.
- **Kabul:** Bir hafızanın doğruluk ve güven gerekçesi kaynak zinciriyle sunulur; skor bir garanti değil göstergedir.

#### B4-006 — Contradiction, supersession ve review baseline'ı (P0, L)
- **Bağımlılık:** B4-004/005; BR-008/009.
- **İşler:** [ ] Aynı kapsamda çelişen kararlar; zaman olarak yeni ama güveni düşük iddialar; kullanıcı tarafından düzeltilmiş notlar. [ ] Öneri olarak conflict case üret. [ ] Review Center'da ikili kanıt/diff. [ ] Kararı tek taraflı silmeden `disputed/superseded` ilişkisi. [ ] Geri alma.
- **Test:** 'Express→Fastify', geçerli/gelecekte geçerli çelişkiler, iki agent aynı anda farklı bilgi yazıyor, yanlış eşleşen kavramlar.
- **Kabul:** Çelişki sessizce uydurulmuş kesinliğe dönüşmez; onay/ret ve kaynak geçmişi korunur.

#### B4-007 — Retrieval pipeline: FTS+vector+graph+time (P0, XL)
- **Bağımlılık:** B4-004/005; mevcut BR-010/011/012.
- **İşler:** [ ] Mevcut FTS5 sıralaması üzerine semantik, graph adjacency, zaman ve güven filtrelerini ölçerek ekle. [ ] Rerank ve query expansion yalnız fayda kanıtıyla. [ ] İlgili parça → kaynak not → oturum/devir geçmişi. [ ] Başlık/etiket/jargon/Türkçe ve kod sembol sorguları. [ ] Sorgu öncesi izin filtreleme (sonradan kozmetik gizleme değil).
- **Test:** Relevance, yanlış eski karar, source leakage, `unavailable` semantic, indeks yeni/kirli; farklı budget koşulları; benchmark `Recall@k`, `MRR`, answer/task accuracy, P95.
- **Kabul:** Mevcut BR-011/012 değerlendirmesinde açıklanamayan regresyon yok; güncel kararlar öncelikli; kaynak kapsamı yetkiye uygun.

#### B4-008 — Persistent Session Search ve tarih filtresi (P1, L)
- **Bağımlılık:** B4-007; BR-018.
- **İşler:** [ ] Saklanmasına açık izin verilen oturum kaynaklarını indexle. [ ] Session/day/provider/project filtresi ve ilgili olay parçaları. [ ] Özet araması ile ham arşiv aramasını ayrı göster. [ ] Retention dolduğunda indeks/önizleme temizliği. [ ] Imported/real event ayrımı.
- **Test:** Ham transcript kapalı olan kullanıcıdan ham arşiv dönmemesi; izin iptali; 100 oturumdan doğru kaynak; tekrarlı import.
- **Kabul:** “Bu sorunu hangi oturumda çözmüştük?” sorgusu tarih ve kaynak etiketiyle cevaplanabilir; izinsiz döküme erişilemez.

#### B4-009 — Context Packs ve continuation capsule (P0, M)
- **Bağımlılık:** B4-007.
- **İşler:** [ ] Mevcut `respected_recall` kısa/summary/full akışı korunur. [ ] Aktif hedef, son iş, karar, öğrenim, açık sorular ve güven bayrakları küçük geçiş paketine ayrılır. [ ] `budget_tokens` ve seçili agent/proje/kasa kapsamı. [ ] Context paketinin SHA ve generation metadata'sı.
- **Test:** 60/120/600/4000 gibi bütçeler, büyük vault, yanlış scope, çoklu agent devamı.
- **Kabul:** Paket gereksiz geçmiş olmadan görev devamına yeterli bağlam verir; veri sızdırmadan, yeniden üretilebilir.

#### B4-010 — Knowledge Synthesis ve concept distillation (P1, L)
- **Bağımlılık:** B4-003/004/005.
- **İşler:** [ ] Günlüklerden kavram notu ve ADR sentezi; benzer bilgilerden özet, bağlanan kaynaklar. [ ] Üretilmiş sentez `model_inferred` olur. [ ] İki kaynağın çelişkisi varsa sessiz birleşme yok. [ ] Yeni sentez eski manuel notu overwrite etmez.
- **Test:** Birbiriyle çelişen üç günlük, kaynak silinmiş, uzun repo notları, kaynakça bağlantıları.
- **Kabul:** Üretilen sentezin her önemli iddiası kaynaklara geri izlenebilir ve insan düzeltmesiyle güncellenebilir.

#### B4-011 — Vault Doctor / lint / orphan / duplicate / merge (P1, L)
- **Bağımlılık:** B4-004; B3-011.
- **İşler:** [ ] Kırık bağlantı, eski dosya, duplicate, orphan, kayıp kaynak, bozuk frontmatter, çelişki raporu. [ ] Düzeltmeleri önizleme + explicit apply. [ ] İki notu birleştirirken eski path redirect/references, kaynak metadata, history. [ ] Dry-run ve backup.
- **Test:** Merge sırasında crash, eşzamanlı edit, binary dosya, bozuk encoding; 1k duplicate ve yanlış pozitif.
- **Kabul:** Varsayılan audit salt okunur; düzeltme sırasında kaynak kaybı ve sessiz silme yok.

#### B4-012 — Obsidian compatibility / graphs / views (P1, M)
- **Bağımlılık:** B4-004/011.
- **İşler:** [ ] Wiki link, frontmatter ve Obsidian ile iki yönlü uyum. [ ] Notlar için graph explorer, renk/filtre, proje/karar/tarih lensleri. [ ] Obsidian arayüzü kurulu değilse Brain kendi notlarını yine gösterir. [ ] Obsidian Bases/Canvas özel entegrasyonu opsiyonel.
- **Test:** Obsidian düzenleme → Brain index tazeliği; Brain'den düzenleme → Obsidian parse; farklı locale/path.
- **Kabul:** Obsidian yazılımı zorunlu değil; kullanıcı notları standart Markdown olarak kalır.

#### B4-013 — Kaynaklardan içe alma: belge/URL/repo/medya (P1, XL)
- **Bağımlılık:** BR-018; B4-003/005.
- **İşler:** [ ] TXT/Markdown/HTML/PDF kaynak parser'ları ve MIME/size/time limit. [ ] Ses/video için **isteğe bağlı transkript bağlantısı**, otomatik harici servis zorunlu değil. [ ] Orijinal kaynak ve çıkarılmış metnin ayrılması. [ ] URL SSRF/redirect/DNS/TLS kontrollerini koru. [ ] İçe alma önizleme, izin, seçici apply, duplicate hash.
- **Test:** Çok büyük dosya, PDF şifresi, bozuk MIME, 127.0.0.1/metadata IP SSRF, karışık IP yanıtı, prompt injection, rate limit, izinsiz bulut gönderimi.
- **Kabul:** Kaynak türleri belgeli; parse edilemeyen dosya sessizce başarılı görünmez; gizli kaynak varsayılan yerel kalır.

#### B4-014 — Import/export ve portability (P1, L)
- **Bağımlılık:** B4-003/004/011.
- **İşler:** [ ] Markdown + metadata manifest + JSON (gerekirse GraphML/Neo4j ayrı adapter) export. [ ] Kaynak bağlantıları ve tarih korunur. [ ] Bağımsız temiz kasaya yeniden içe alma. [ ] Machine-specific secret veya veritabanı cache export edilmez. [ ] Export preview ve content policy.
- **Test:** İhracat→içe alma→yapısal eşitlik; çakışan UUID/path; malicious zip traversal; düşük disk alanı.
- **Kabul:** Kullanıcı Brain'i bıraktığında hafızasını standart biçimde taşıyabilir; secret'lar varsayılan dışa aktarımda yok.

#### B4-015 — Multi-agent event & contribution ledger (P1, L)
- **Bağımlılık:** B4-003/009.
- **İşler:** [ ] Agent kimliği, oturum, kaynak dosya, üretilmiş karar, teslim edilen not. [ ] Append-only olay ilişkileri ve kullanıcı düzeltme olayları. [ ] Olaylara yetkili arama ve timeline. [ ] Kayıt kapsamı: hafıza ve bilgi devirleri; görev scheduler yok.
- **Test:** Aynı agent farklı projede, aynı olay 2 kez, agent identity spoofing, eski index, event ordering.
- **Kabul:** 'Hangi agent bu bilgiyi ne zaman bıraktı?' kaynaklı sorgusu mümkün; agent kontrol paneline dönüşmez.

#### B4-016 — Agent handoff foundation ve artifact reference (P1, M)
- **Bağımlılık:** B4-009/015.
- **İşler:** [ ] Devam kapsülü formatı ve `handoff_id`, kaynaklar, yetkili hedef agent, açık işler, güven durumu. [ ] Dosya değişiklikleri için sadece hash/path/reference; büyük artefaktları Brain içine kopyalamak şart değil. [ ] Orchestrator RPP sözleşmesine uygun salt okunur teslimat. [ ] Kullanıcı seçimiyle paylaşım.
- **Test:** İzin iptali, devralan agent değiştirilmesi, kısmi başarılı görev, kayıp artefakt, yanlış proje.
- **Kabul:** Geri çağrılabilen yapılandırılmış devir kaydı var; görev dağıtma Orchestrator'da.

#### B4-017 — Learned lessons + approval baseline (P1, M)
- **Bağımlılık:** B4-010/011 ve BR-009.
- **İşler:** [ ] Tekrarlanan hata/başarı adayları, destekleyen oturumlar, kapsam, güven ve önerilen kural. [ ] Promotion yalnız insan onayıyla. [ ] Skill üretimi için metadata/versiyon hazırlığı. [ ] Yanlış/çelişkili pattern'ı reddet/geri al.
- **Test:** Bir kerelik yanıltıcı başarı, beş tekrar, kaynakları silinmiş pattern, prompt injection.
- **Kabul:** Öğrenim taslağı oluşturulur ama hiçbir agent'a otomatik yetkili talimat olarak yüklenmez.

#### B4-018 — Search & graph Desktop UI (P0, L)
- **Bağımlılık:** B4-004/007/012.
- **İşler:** [ ] Graph Explorer, timeline filter, related source drilldown, search reason açıklaması. [ ] Token/context seçici. [ ] Binlerce düğümde lazy loading. [ ] Ekranların boş/bozuk/izin reddi durumları.
- **Test:** Büyük graph, offline, eksik source, uyarı focus/readability.
- **Kabul:** Kullanıcı not ve karar ilişkilerini uygulama içinde izleyebiliyor; veritabanı taşıma yüzünden donma yok.

#### B4-019 — Review, conflicts ve vault operations UI (P0, M)
- **Bağımlılık:** B4-006/011.
- **İşler:** [ ] Kural/karar/çelişki inceleme, evidence diff, onay/reddet, birleşme önizleme. [ ] Zaman etkisi, geri alma ve audit kayıtları. [ ] Geri alınamaz eylem öncesi açık onay.
- **Test:** Çift onay/yarış, yanlış vault, Undo, çok büyük diff.
- **Kabul:** UI, CLI'nin güvenlik sınırından daha geniş izin kazanmaz.

#### B4-020 — Knowledge source / research UI (P1, M)
- **Bağımlılık:** B4-013/014.
- **İşler:** [ ] Kaynak ekle, parse/önizleme, izin, ilerleme, başarısızlık nedeni, duplicate durumu. [ ] Kaynağı ve türetilen notu yan yana gör. [ ] Dış ağa veri gönderimi görünür.
- **Test:** URL blok, offline, 50 MB sınır senaryosu, erişilmeyen belge.
- **Kabul:** Kullanıcı hangi kaynağın nasıl hafızaya dönüştüğünü anlıyor ve geri alabiliyor.

#### B4-021 — Built-in memory operation commands / skills parity (P1, L)
- **Bağımlılık:** B4-011/017.
- **İşler:** [ ] Rakiplerdeki komutları isim isim registry'de eşle (ör. `wiki-lint`, `wiki-digest`, `obsidian-reconcile`, `session-search`, `vault-skill-factory`). [ ] Aynı davranışı gereksiz 50 komut yerine alan bazlı CLI/MCP/UI ile sun; kalan işlevsel boşluklara ayrı command ekle. [ ] Basit `doctor`, `reindex`, `recap`, `merge-preview`, `export`, `import` eylemleri.
- **Test:** Her eşlenen rakip davranışı için fixture+expected result; izin ve dry-run.
- **Kabul:** İsim sayısı değil işlev eşitliği; registry'de her hedef davranışın testi bulunuyor.

#### B4-022 — Profil, kişi/proje ve geçerli tercih hafızası (P1, L)
- **Bağımlılık:** B4-003/005.
- **İşler:** [ ] Kullanıcı çalışma tercihleri, projeye özel konvansiyonlar, takım bağlamı, hedefler, active thread. [ ] Profil otomatik çıkarımı `suggested`/`inferred`; approval without override. [ ] Proje sınırlarını ve özel not yetkilerini koru.
- **Test:** Farklı projelerde çelişen stil/komutlar; kullanıcı tercihi güncellendi; özel proje notu global bağlama sızmadı.
- **Kabul:** 'Projem A'da X kullanıyoruz, B'de Y' doğru kapsamda hatırlanıyor.

#### B4-023 — Benchmark parity harness ve bağımsız kanıt (P0, L)
- **Bağımlılık:** B4-001/002/007.
- **İşler:** [ ] Her hedef capability için karşılaştırmalı vaka. [ ] Rakip bağımlılıklarının kurulum/ücret/izin ve destek sınırlarını not et. [ ] Test pass/fail ve manuel doğrulama ayrımı. [ ] İsimli rakip başarısını README iddiası diye etiketle, test edilmediyse kıyas yapma.
- **Test:** 17 rakip envanterinden rastgele örnek audit; test vakanın kaynağı/capability açıklaması; boş testli feature gate fail.
- **Kabul:** Her hedef hafıza capability'sinin en az bir otomatik veya gerçek kullanım kanıtı var, açıklanan istisnalar açık.

#### B4-024 — Güvenlik/mahremiyet ve performance regression (P0, L)
- **Bağımlılık:** B4-003…023.
- **İşler:** [ ] Kaynak prompt injection, graph poisoning, false provenance, data egress, token/cost, replay/archive, izin izolasyonu. [ ] Markdown graf rebuild zaman/bellek; çok notlu kasa; sidecar+UI cevaplanabilirlik. [ ] Kritik hak ihlali fail-closed.
- **Test:** Attack fixtures; kaynak değiştirme, stale izin; 10k not/50k edge gibi **önerilen sentetik ölçek**. Gerçek sınır baseline'a göre ayarlanır.
- **Kabul:** P0 güvenlik/kasa kaybı yok, kalite göstergelerinde açıklanamayan regresyon yok.

#### B4-025 — Beta.4 parity review & yayın kapısı (P0, M)
- **Bağımlılık:** B4-001…024.
- **İşler:** [ ] Registry hedeflerinin 100% durum değerlendirmesi. [ ] Çekirdek hafıza scope ve desktop UX tamam. [ ] Eksikler ya uygulandı ya da ürün sahibinin açık kararına girdi. [ ] Beta.5 veri/API bağımlılıkları hazır. [ ] Uygulanan her modül için migration/backup/installer/docs tests.
- **Kabul:** Beta.4 'rakiplerin tüm özelliklerini inceledik' diyebilecek kanıt envanterine sahip; 'tüm yazılım kategorilerini Brain'e gömdük' gibi yanlış iddia yok. Hedef hafıza kabiliyetlerinin her biri kabul/testten geçmiş.

### E.6. Beta.4 alan dışı yetenekleri nasıl ele alacağız?

- **Takvim, Telegram, podcast, browser automation:** Genel yardımcı uygulamaya dönüşmek yerine **isteğe bağlı kaynak bağlayıcısı**; kalıcı karar/hafıza öğesi üretme işlevi değerlendirilebilir. Otomasyonun kendisi Brain içine alınmaz.
- **Agent ekip kurma, paralel kod yazdırma, görev çalıştırma, PR açma:** Orchestrator işi; Brain yalnız geçmiş bilgi, karar, handoff ve source evidence sağlamakla sorumlu.
- **MCP/skills mağazası, eklenti kurulum pazar yeri:** Hub işi; Brain kendi memory skill/adapter config'lerini yönetebilir.
- **Tam IDE ve kod değişiklik diff'i:** Codebase Memory MCP/Graphify/Serena benzeri sistemlerle istemci üzerinden entegre edilir; Brain tüm AST motorunu yeniden yazmak zorunda değil. Hafıza kararlarını dosya/symbol referansına bağlayabilir.
- **Kişisel CRM, görev panosu, sosyal medya:** Doğrudan Brain hafıza misyonuyla ilgisiz; araştırılır ve registry'de gerekçeli karar alır. Bu yeteneklerin varlığı Brain'in parity başarısını belirlemez.
- **Hosted/sync/cloud:** V1.0 için zorunlu varsayma. Kullanıcı değeri, E2EE, maliyet, threat model, veri sahipliği ve privacy testleri olmadan otomatik cloud sync eklenmez; isteğe bağlı export/backup ilk önce gelir.

---

## F. BETA.5 — ONAYLANAN 10/10 FARKLILAŞTIRICI ÖZELLİK

**Ürün sahibi kararı:** Aşağıdaki on özelliğin **tamamı** Beta.5 hedef kapsamındadır; 'opsiyonel fikir' statüsüne geri düşmez. Beta.4'te temel mekanizma zaten varsa yeniden yazılmaz, üst düzey kullanıcı akışı ve ürün değeri geliştirilir. Farklılık iddiası rakip kanıtı ve kullanıcı değerlendirmesi olmadan pazarlama gerçeği olarak kullanılmaz.

**Geliştirme sırası:** `B5-01 Evidence Chain` ve `B5-02 Privacy Firewall` → `B5-03 Conflict Resolver` → `B5-04 Verified Handoff` → `B5-05 Replay` → `B5-06 Time Machine` → `B5-07 Freshness` → `B5-08 Impact` → `B5-09 Observatory` → `B5-10 Skills Lab`. Bazı UI/benchmark işleri paralel yürütülebilir.

### B5-01 — Memory Evidence Chain (P0, L)

- **Kullanıcı problemi:** 'Brain bunu nereden öğrendi? Güvenebilir miyim? Kaynak değişmiş mi?'
- **Örnek:** `Ödemeleri INTEGER kuruş ile saklayacağız` kararı; kaynak oturum, commit/ADR, kullanıcı onayı, değişiklik tarihi ve kaynak hash durumuyla gösterilir.
- **Beta.4 bağımlılıkları:** B4-003/004/005/018; mevcut BR-007/008.
- **Python motoru:** `trace_memory(memory_id)` tarzı sorgu; iddiadan kaynağa çok adımlı provenance zinciri; `observed/derived/approved/superseded` edges; source digest ve missing source; hash recheck; zaman sınırları.
- **Desktop:** Kanıt zinciri paneli; kaynak→özet→karar→agent hattı; güven statüsü; bozuk/kayıp kaynak uyarısı; ilgili diff; onay geçişleri.
- **Güvenlik:** Hassas kaynak gövdesi izinsiz gösterilmez. Kaynak linki yalnız izinli kasa/URL. 'Model bunu iddia ediyor' ile 'kullanıcı onayladı' karıştırılmaz.
- **Testler:** (1) 3 adımlı kaynak zinciri. (2) Kayıp/eski hash. (3) Source spoof. (4) Başka projenin özel kaynağı. (5) Aynı iddiaya çelişkili iki kaynak.
- **Ölçüm/kanıt:** Provenance completeness; kaynak bağlantısı doğruluğu; false verified oranı; raporla.
- **Kabul:** Kritik hafızanın iddia ve kaynak ilişkisi tıklanabilir ve denetlenebilir; kaynağı bulunmayan hafıza kesin onaylı gibi gösterilmez; yetkisiz kaynak ifşa olmaz.

### B5-02 — Memory Privacy Firewall (P0, XL)

- **Kullanıcı problemi:** 'Hangi agent/model hangi hafızamı görebiliyor ve verilerim nereye gidiyor?'
- **Örnek:** Kişisel notlar yalnız yerel işlemde; A projesi yalnız Claude/Codex'e; OpenRouter özetleyici sadece kullanıcı onaylı kaynakla çalışır.
- **Beta.4 bağımlılıkları:** B4-003/005/007; mevcut RPP/MCP izinleri; B3 Settings.
- **Python motoru:** Deny-by-default policy evaluator; `vault/project/note-label/source-type/agent/provider/operation` boyutları; `read/search/summary/export/egress/write` ayrı haklar. **Pre-retrieval** ve **pre-provider-send** kontrolleri; servis katmanında tek kapı. Default local-only / explicit opt-in; revocation; sanitized audit ledger.
- **Desktop:** Scope matrisi, 'Şu agent neleri görür?' simülasyonu, her outbound gönderim için açık kategori/sağlayıcı izinleri, gizli not etiketleri, kullanım geçmişi.
- **Güvenlik:** Frontend yetki kontrolü tek başına yeterli değil; Python enforcement şart. İzin iptali eski MCP oturumlarına da anında uygulanır. Ağ yanıtı/exception log'una secret kaçamaz.
- **Testler:** (1) Aynı PC iki agent farklı scope. (2) Proje değişimi. (3) Clipboard/export redaction. (4) Paid provider fallback reddi. (5) Revoked token/old process. (6) Kısmi IPC ve doğrudan CLI bypass. (7) Yanlış kasa UUID.
- **Ölçüm/kanıt:** Policy bypass testlerinde 0 başarılı yetkisiz erişim; izin kontrolü p95 ek maliyeti; false denial raporu.
- **Kabul:** Yanlış scope'taki veri search/context/summary/egress/export üzerinden sızmaz; UI'daki politika ile motor kararı eşleşir; veri dışa çıkışı izinli ve denetlenebilir.

### B5-03 — Memory Conflict Resolver (P0, XL)

- **Kullanıcı problemi:** İki agent/proje oturumu farklı kararlar tutuyor; hangisi güncel, neden değişti?
- **Örnek:** Claude 'Express', Codex 'Fastify' yazdı. Brain iki iddiayı tarih, proje, onay ve kaynaklarıyla karşılaştırıp kullanıcıya geçerli kararı seçtirir.
- **Beta.4 bağımlılıkları:** B4-004/005/006; B5-01; mevcut BR-008/009.
- **Python motoru:** Olay/kapsam-temelli contradiction detection; gerçek çelişki ile farklı proje/gün/ortam farkını ayır. `merge`, `supersede`, `keep_both_scoped`, `mark_unresolved`, `reject`, `revert` transaction. Karar değişikliğinde dependent cache invalidate.
- **Desktop:** Yan yana evidence diff, timeline ve 'nerede geçerli?' alanı. Tek tık 'otomatik çöz' varsayılan olmaz; öneriyle insan onayı.
- **Güvenlik:** Model çıktısı tek başına kullanıcı kurallarını geçersiz kılamaz; rollback/causal log var.
- **Testler:** (1) Aynı projede gerçek çelişki. (2) İki ayrı projede meşru fark. (3) Tarihsel karar. (4) Unverified ve verified karşılaşması. (5) UI double-submit. (6) Harici not edit yarışması.
- **Ölçüm/kanıt:** Conflict precision/recall; yanlış birleşme (false merge) kritik metrik.
- **Kabul:** Kaynağa dayalı çözüm ve geri alma; belirsizlikte unresolved; aktif karar aramada güncel; geçmiş kayıtlar silinmez.

### B5-04 — Verified Agent Handoff (P0, XL)

- **Kullanıcı problemi:** Claude'da bırakılan işi Codex'e baştan anlatmak zorunda kalmak; yanlış/eski bağlam aktarmak.
- **Örnek:** Claude auth middleware'ini değiştirdi, testler eksik; Codex'e doğrulanmış karar, ilgili dosya, açık iş, çözülmüş hata, test kanıtları veriliyor.
- **Beta.4 bağımlılıkları:** B4-009/015/016; B5-01/02.
- **Python motoru:** `prepare_handoff` (source agent/session/project, target, intent, budget), `inspect_handoff`, `consume_handoff`, `invalidate_handoff`. Handoff version/hash, kaynak/scope, approved facts, unresolved warnings, relevant paths; stale TTL/validation. `unverified` bilgi uyarıyla gelir.
- **Desktop:** Kaynak/ hedef agent seç, aktarılan bilgi önizle, sensitive satırları çıkar, kullanıcı onayı, devir geçmişi.
- **Güvenlik:** Hedef provider farklı trust scope ise Privacy Firewall filtrelemeli; agent yürütme / PR açma Brain'in değil Orchestrator'ın işi.
- **Testler:** (1) Claude→Codex gerçek canlı devri. (2) Hedef agent yok. (3) Scope/TTL aşıldı. (4) Devirden sonra karar değişti. (5) Kaynak dosya hash değişti. (6) Offline.
- **Ölçüm/kanıt:** Handoff completion rate, görev başarısı, context tokenı ve tekrar anlatım süresi karşılaştırması.
- **Kabul:** Hedef agent gerçek testte ilgili geçerli kararları uygular; paket izin ve kaynaklarla açıklanabilir; görev sorumluluğu Orchestrator'a kaymaz.

### B5-05 — Memory Replay & Simulator (P0, XL)

- **Kullanıcı problemi:** 'Şu isteği Codex'e versem Brain hangi notları ve neden getirecek? Hata riski var mı?'
- **Örnek:** Kullanıcı `Yeni migration yaz` prompt'u ve hedef agent seçer; 600 token bütçesinde kaynakları, stale ve private excluded notlarını görür.
- **Beta.4 bağımlılıkları:** B4-007/009/023; B5-01/02/04.
- **Python motoru:** Salt-okunur `simulate_retrieval` / `replay_context` API; deterministik snapshot (vault index version, query, model/ranker version, permission profile, time anchor, budget). Gerçek tool/agent çalıştırma **varsayılan yok**. A/B kıyasları; dry-run; explanation.
- **Desktop:** Prompt gir, agent/proje/tarih/limit seç, oluşturulacak context diff, excluded reason, token estimate, source chain, stale/private uyarıları.
- **Güvenlik:** Simülasyon asla kullanıcı kasasına, agent ayarlarına veya geçmişe yazmaz; yetki dışı sonuçları 'gizli öğe var' diyerek bile sızdırmamaya dikkat et.
- **Testler:** (1) Aynı snapshot aynı context. (2) Önizleme sonrası kasa hash değişmiyor. (3) Privacy filtre. (4) Index update ile snapshot farkı. (5) No memory ve budget 60 senaryosu.
- **Ölçüm/kanıt:** Simülasyon/gerçek retrieval uyumu; token tahmin hata oranı; işlem süresi.
- **Kabul:** Dry-run tekrarlanabilir ve salt okunur; kullanıcı context'i ve dahil edilme sebeplerini anlayabilir; yan etki yok.

### B5-06 — Memory Time Machine (P1, XL)

- **Kullanıcı problemi:** '15 Ekim'de proje nasıl çalışıyordu; hangi kararlar ne zaman değişti?'
- **Örnek:** Proje 15 Ekim'de Express kullanıyordu, 24 Ekim'de Fastify'a geçti. Geçmiş zamana ait sorular doğru geçerlilik penceresinden yanıtlanır.
- **Beta.4 bağımlılıkları:** B4-004, B4-006, B4-008/018; B5-01.
- **Python motoru:** `as_of` sorgu, valid-time vs record-time ayrımı, audit-snapshot veya event sourcing mümkünlük analizi. Sadece mevcut olay kaydının desteklediği geçmişi oluştur; eksik tarih için sahte reconstruction yapma. Reversible diff ve source references.
- **Desktop:** Tarih/saat seçici, bu tarihteki facts/decisions, önce-sonra diff, değişiklik nedeni, kaynak, belirsiz rekonstrüksiyon uyarısı.
- **Güvenlik:** Silinmiş/retention süresi dolmuş hassas veri Time Machine ile geri sızdırılmamalı. İzin revocation geçmiş sorguya da uygulanmalı.
- **Testler:** (1) Backdated import. (2) Future valid decision. (3) Same-day conflicting events. (4) Timezone ve DST. (5) Retention purge. (6) Kaynak yoksa belirsizlik.
- **Ölçüm/kanıt:** As-of accuracy, provenance completeness, stale leakage.
- **Kabul:** Bilinen geçmiş doğru tekrar kuruluyor; bilinmeyen geçmiş 'kayıt yok' olarak işaretli; eski silinmiş özel veri geri açılmıyor.

### B5-07 — Memory Freshness Guardian (P1, L)

- **Kullanıcı problemi:** Node/API/çalışma ortamı değiştiği halde Brain eski kuralı kullanıyor.
- **Örnek:** Node 20→22 geçişinde sürüme bağlı build kuralları incelemeye alınır; otomatik silinmez.
- **Beta.4 bağımlılıkları:** B4-003/004/005/011/022; B5-01/03.
- **Python motoru:** Değişebilir kaynak sinyali (dosya hash/manifest package version/repo ref ve varsa isteğe bağlı web check); TTL/review interval policy; otomatik `needs_review` önerisi. Kritik değeri doğrulamadan `stale` kararı verme.
- **Desktop:** Eski/şüpheli bilgileri neden, kaynak, son doğrulama ve etkilenen notlar ile listele; toplu review; snooze/accept.
- **Güvenlik:** Kaynak yenilemesi izinli; bulut URL erişimi ve gizli proje bilgisi dışa çıkışı açık kontrole tabi.
- **Testler:** (1) Gerçek sürüm değişimi. (2) Aynı sürüm kontrolü. (3) Dış kaynak 404. (4) Offline. (5) İzin iptali. (6) Yanlış pozitif.
- **Ölçüm/kanıt:** Stale discovery precision, false alarms, onay oranı.
- **Kabul:** Tespit kaynak/koşul ile açıklanabilir; sessiz imha yok; doğrulaması yapılmamış eski bilgi güncel kesinlikte sunulmaz.

### B5-08 — Memory Impact Advisor (P1, XL)

- **Kullanıcı problemi:** Bir mimari karar değiştirildiğinde hangi hafıza ve notların etkilendiği anlaşılmıyor.
- **Örnek:** JWT→session cookie geçişi; etkilenebilecek auth notları, geçmiş kararlar, riskler ve opsiyonel dış kod grafından işaretlenen dosyalar gösterilir.
- **Beta.4 bağımlılıkları:** B4-004/006/011, opsiyonel Codebase Memory MCP/Graphify adapter; B5-01/03/07.
- **Python motoru:** Graph traversal ile etki adayları, bağımlılık türü/güven puanı; 'kesin etkilendi' değil 'kontrol edilmeli' ayrımı; ilgili kaynak ve tarih. Dış kod analizi varsa opsiyonel read-only adaptör, varsayılan AST sunucusu zorunlu değil.
- **Desktop:** Etki haritası, önem sırası, kaynak/açık iş filtresi, kullanıcıya onaylı güncelleme planı; istenirse Orchestrator'a yalnız bilgi paketi.
- **Güvenlik:** Tavsiye otomatik kod veya kural değişikliği yapmaz; dış tool çağrılarında onay.
- **Testler:** (1) Çok bağlantılı karar. (2) Cycle. (3) Kayıp source. (4) Yanlış scope. (5) Graph rebuild. (6) Code graph adaptörü absent.
- **Ölçüm/kanıt:** Impact recall/precision ve kullanıcı inceleme süresi.
- **Kabul:** Etki adayları açık kanıtla gösterilir; false certainty yok; diğer projelere izinsiz erişim yok.

### B5-09 — Memory Quality Observatory (P1, L)

- **Kullanıcı problemi:** 'Brain gerçekten işime yarıyor mu; hangi agent daha iyi hatırlıyor; maliyeti nedir?'
- **Örnek:** Testte 80 sorudan 74 doğru; 4 stale, 2 missing. Kullanıcı bunun sentetik/gerçek test türünü, örneklemi ve tarihini görür.
- **Beta.4 bağımlılıkları:** B4-023/024; mevcut BR-001/002/003 ve B3 Dashboard; B5-05.
- **Python motoru:** Privacy-preserving aggregates: retrieval accuracy, stale-rate, source coverage, context tokens, provider costs, p95, usage/failure reason. Ayrı `synthetic`, `manual-real`, `live-opt-in` kaynak sınıfları. Log sanitization, retention, yalnız local varsayılan.
- **Desktop:** Graf/filtre (zaman, model, provider, proje), benchmark vs gerçek görev ayırımı, baseline karşılaştırması, sınırlama açıklamaları.
- **Güvenlik:** Varsayılan otomatik telemetri dışa çıkışı yok; küçük örneklemlerde yanıltıcı genelleme uyarısı. API token/ham prompt asla panelin metrik kaydına yazılmaz.
- **Testler:** (1) Verisiz dashboard. (2) Çok az örnek. (3) Yanlış JSON/bozuk metrik. (4) Farklı benchmark dataları birleştirme hatası. (5) Opt-out.
- **Ölçüm/kanıt:** Metrik hesabının fixture oracle ile eşleşmesi; rapor repeatability.
- **Kabul:** Her göstergeye kaynak dataset, zaman ve ölçüm türü ekli; uydurma yüzde ve karışık benchmark yok.

### B5-10 — Memory Skills Laboratory (P1, XL)

- **Kullanıcı problemi:** Tekrarlanan başarılı iş akışları yeniden kullanılabilir beceriye dönüşmüyor; yanlış kural otomatik yüklenirse güvenlik riski oluşuyor.
- **Örnek:** Beş farklı oturumda başarıyla geçen deployment checklist'i kaynaklı `SKILL.md` taslağına dönüşür; test ve insan onayından sonra seçili agent/projede etkinleştirilebilir.
- **Beta.4 bağımlılıkları:** B4-010/017/021; B5-01/02/03/09.
- **Python motoru:** Observations→candidate pattern→skill draft, kapsam/önkoşul/istisna/test fixture/güven bilgisi. Skill version, source hash, rollback; review/promotion. Otomatik yürütülebilir script veya dış bağlantı üretimine sıkı yetki kontrolü. Agent-specific skill format adapter yalnız açık kullanıcı seçimiyle.
- **Desktop:** Skill adayları, örnek oturumlar, önerilen prosedür, simüle/test et, onayla/geri al, hedef agent scope'u, başarı/başarısızlık geçmişi.
- **Güvenlik:** Ham dökümdeki kötü niyetli talimat skill'e yükseltilemez; kesin onay öncesi kurulum yok; dış agent'ın workspace'e izinsiz yazma hakkı kazanılmaz.
- **Testler:** (1) Aynı başarının tekrarı. (2) Tekil anekdot. (3) Yanlış sınıflandırılmış örnek. (4) Prompt injection. (5) Skill güncelleme ve geri alma. (6) Agent-specific adapter fail.
- **Ölçüm/kanıt:** Skill adoption success, task pass delta, yanlış skill önerisi oranı, skill drift testleri.
- **Kabul:** Her skill önerisi izlenebilir, test edilebilir, geri alınabilir; onaysız otomatik etkinleştirme veya yetki genişletme yok.

### F.1. Beta.5 ek görevler — on özelliği tek ürün deneyimine dönüştür

#### B5-11 — Ortak izin/provenance/UX dili
- [ ] Her özellik aynı `vault_uuid`, source, trust, time, approval, permission semantics kullanmalı; özel çözümler veri şemasını parçalamamalı.
- [ ] Ortak tasarım bileşenleri: `SourceChip`, `TrustIndicator`, `TimeRange`, `PermissionPreview`, `DiffViewer`, `RiskWarning`, `ReviewAction`.
- [ ] UI ve CLI/MCP sonuçları aynı domain servisinden türetilmeli; aksi halde Simulator ile gerçek context farklılaşır.
- **Kabul:** 10 özelliğin statü/izin/tarih terimleri tutarlı; modal ve bildirim erişilebilir.

#### B5-12 — Her özellik için gerçek demo ve parity audit
- [ ] On özellik için her biri minimum bir gerçek kullanıcı senaryosu ve bir kötü durum senaryosu; demo kayıtları özel kullanıcı kasasıyla değil fixture ile oluşturulur.
- [ ] Rakiplerde benzer işlev varsa kendi ürünümüzün farkını `hypothesis/test/result` ile ayır; 'rakipte yok' iddiası bağımsız kanıt olmadan kullanılmaz.
- [ ] Benchmark, UX geri bildirimi ve kötü durum raporu evidence dizininde saklanır.
- **Kabul:** `10/10` feature acceptance geçmeden beta.5 feature-complete etiketi yok.

#### B5-13 — Beta.5 göç/kurtarma ve izin regresyonu
- [ ] Beta.2/3/4 kasalarından beta.5'e migration fixture. [ ] Graph ve source metadata rebuild. [ ] UI eksik/bozuk/new fields compat. [ ] Revoke/privacy/purge eski memory snapshot üzerinde de çalışmalı.
- **Kabul:** Veri kaybı yok, migration atomik/geri alınabilir, deny-by-default korunuyor.

### F.2. Beta.5 on özelliğin kabul checklist'i
- [ ] Evidence Chain: kaynak bütünlüğü ve kaynak yok uyarısı.
- [ ] Privacy Firewall: tüm veri yollarında fail-closed scope/egress.
- [ ] Conflict Resolver: kaynaklı, geri alınabilir, yanlış kapsamı birleştirmeyen çözüm.
- [ ] Verified Agent Handoff: gerçek farklı agent ile bilgi devri.
- [ ] Replay & Simulator: salt-okunur, tekrarlanabilir bağlam önizleme.
- [ ] Time Machine: doğru as-of ve retention-güvenlik.
- [ ] Freshness Guardian: kaynaklı güncellik uyarısı, sessiz silme yok.
- [ ] Impact Advisor: etkileri öneri/kanıt ayrımıyla gösterme.
- [ ] Quality Observatory: sentetik ve gerçek sonuçları ayıran doğru metrikler.
- [ ] Skills Laboratory: kaynaklı, testli, insan onaylı ve geri alınabilir skill.

**Beta.5 Gate:** On madde tamam, UI/CLI/MCP izin uyumluluğu testli, karşılaştırmalı ürün değerinin ilk delilleri var. Daha ileri istatistiksel değerlendirme beta.6'da derinleşir.

---

## G. BETA.6 — BİLİMSEL ARAŞTIRMAYLA VE GERÇEK DÜNYA VERİLERİYLE OPTİMİZASYON

**Hedef:** Beta.2'den Beta.5'e kadar geliştirilen **tüm** çekirdek/parity/özgün özelliklerin verim, doğru eylem, güvenilirlik, mahremiyet ve kullanılabilirliğini ölçmek; daha iyi olduğunu kanıtlayamadığımız optimizasyonu varsayılan haline getirmemek.

### G.1. Kullanılacak araştırmalar — neyi söyledikleri ve Brain'e somut etkileri

| ID | Araştırma ve kaynak | Desteklediği soru | Brain'de doğrulanacak deney |
|---|---|---|---|
| R01 | **LongMemEval**, Wu ve ark., ICLR 2025, https://proceedings.iclr.cc/paper_files/paper/2025/hash/d813d324dbf0598bbdc9c8e79740ed01-Abstract-Conference.html | Bilgi çıkarma, çoklu oturum, zaman, güncelleme, abstention | Beş kategoride retrieval ve final answer başarı oranı |
| R02 | **LongMemEval-V2**, Wu ve ark., 2026, https://arxiv.org/abs/2605.12493 | Ortam durumu, iş akışı, tekrar eden hata, premise awareness | Kod geliştirme oturumundan gerçek iş akışı bilgisini aktarabilme |
| R03 | **Zep: A Temporal Knowledge Graph Architecture**, Rasmussen ve ark., 2025, https://arxiv.org/abs/2501.13956 | Zamanla değişen bilgiyi graf olarak yönetme | As-of, supersedes, conflicting timeline doğruluğu |
| R04 | **Hindsight**, Latimer ve ark., ACL 2026, https://aclanthology.org/2026.acl-demo.27/ | Fact, experience, observation, opinion ayrımı ve retain/recall/reflect | Evidence Chain ve kaynak türü ayrımı |
| R05 | **MemGPT**, Packer ve ark., 2023, https://arxiv.org/abs/2310.08560 | Kademeli aktif/harici bellek yaklaşımı | Short/context/full retrieval, token vs task success |
| R06 | **Lost in the Middle**, Liu ve ark., TACL 2024, https://aclanthology.org/2024.tacl-1.9/ | Uzun context'te ilgili bilginin konumu etkisi | Aynı bilgi farklı sıralarda verildiğinde görev başarısı |
| R07 | **MemSecBench**, Chen ve ark., 2026, https://arxiv.org/abs/2607.27080 | Zehirli hafızanın kaydedilip sonradan eyleme yansıması ve onarım | Write→Recall/Execute→Forget zincir testi |
| R08 | **Generative Agents**, Park ve ark., 2023, https://doi.org/10.1145/3586183.3606763 | Gözlem/reflection/planlama hafızası | Tekrarlanan deneyim→öğrenim kalitesi |
| R09 | **Anthropic: Demystifying Evals for AI Agents**, 2026, https://www.anthropic.com/research/demystifying-evals-for-ai-agents | Agent değerlendirme setinin pratik kurulumu | 20–50 gerçek sorunla başlangıç ve büyüyen regresyon seti |
| R10 | **Graphiti** resmî repo, https://github.com/getzep/graphiti | Geçerliliği değişen entity ilişkileri | Temporal graph model alternatifleri ve maliyet |
| R11 | **MemoryArena**, ICML 2026, https://proceedings.mlr.press/v306/he26am.html | Uzun hafıza bilgisini eyleme uygulama | Çok oturumlu görev tamamlama ve bilgi doğru kullanımı |
| R12 | **STATE-Bench**, Microsoft araştırma yazısı, 2026, https://opensource.microsoft.com/blog/2026/05/19/introducing-state-bench-a-benchmark-for-ai-agent-memory/ | Task success/tutarlılık/maliyet/user experience | Farklı tekrar koşularında hedef görev başarı dağılımı |

> Araştırma listesi **Brain'in performansını ispatlamaz**. Her kaynak kendi deney koşullarına sahiptir. Dosyaya `paper result` ve `Brain result` ayrı alanlarda kaydedilir; kaynağın iddia ettiği yüzde Brain'in ölçülmüş yüzdesi olarak yazılamaz. Başka araştırmaları/2026 sonrası güncellemeleri beta.6 başında yeniden tara; doğrulamadan otorite olarak kullanma.

### G.2. Deney tasarımı sözleşmesi

- Her deneyde **hipotez, baseline, değişen tek ana etken, sabit koşullar, veri seti hash'i, model/provider sürümü, decoding ayarı, donanım, OS, Brain commit'i, tekrar sayısı, maliyet, istatistik yöntemi ve fail case** kayıtlı.
- **Görev tamamlanması** ile **retrieval doğruluğu** ayrı: doğru notu bulmak, agent'ın doğru kodu yazdığını kanıtlamaz.
- Gruplar: hafızasız; FTS; semantic; hybrid; graph-temporal; candidate improvement; seçilen rakipler aynı izin/model/bütçeyle mümkünse gerçek kurulumda.
- Her kolda eşdeğer görev ve privacy limitleri uygulanır. Rakibin cloud özelliği varsa üçüncü tarafa gerçek kişisel veri yollamadan synthetic dataset kullan.
- Model/ranker karşılaştırması **gerçek token ve API maliyetini** içerir. Yaşam döngüsü: capture + summarize + index + retrieve + inference + correction maliyeti.
- Örneklem: İlk 50 sentetik hafıza testi regresyon çekirdeği; LongMemEval/LongMemEval-V2 uygun alt kümeleri lisans/araç yeteneğine göre; ek 50+ gerçek dünya anonimleştirilmiş/izinli senaryo. Örneklem sayısı **hedef**; katılımcı ve veri yoksa sonuç uydurulmaz.
- Teknik kalite: per-category pass, answer F1/accuracy, Recall@1/5, MRR, stale error, false merge, abstention, provenance completeness, prompt injection success, task success, user time-to-completion, p50/p95, CPU/RAM/disk/token/para.
- Pilot kullanıcılar için açık, geri alınabilir katılım izni ve mümkünse sadece **yerel anonim metrik**; özel prompt, dosya ve session body telemetri olarak varsayılan toplanmaz.
- 'En iyi' ifadesini mutlak iddia yerine 'bu test ortamında şu metriği şu kadar iyileştirdi' gibi kapsamlı, tekrarlanabilir ifadeye dönüştür.

### G.3. Beta.6 görevleri (B6-001…B6-015)

#### B6-001 — Research register / evidence map (P0)
- [ ] Tüm R01–R12 kaynaklarını yayımlanma tarihi, deney protokolü, çelişen bulgular, metodoloji sınırı ve Brain işleviyle eşleştir.
- [ ] Her beta.4/5 capability'e en az bir kaynak veya gerekçeli mühendislik kararı; ürünün tüm kritik iddialarına ölçüm planı.
- [ ] Yanlış/yeniden yayımlanmış makale veya sürüm bulgularını düzeltme kaydı.
- **Kabul:** Kritik feature için `why` + `what to test` + `how measured` boş değil.

#### B6-002 — Release-frozen benchmark dataset ve anti-leak kuralları (P0)
- [ ] 50 mevcut test + yeni zamansal/iş akışı/güvenlik/abstention + gerçek workflow sentetik örnekleri; private/public set ayrımı.
- [ ] Synthetic/real/red-team kolları; dataset hash ve değişiklik günlüğü.
- [ ] Sistem prompt ve training leakage kaynaklı yanlış karşılaştırmaları azaltmak için gizli holdout.
- **Kabul:** Dataset commit ve sorular etiketli, sonuçların tekrarı mümkün.

#### B6-003 — Capture/summarization karşılaştırması (P0)
- [ ] Hook drop, partial transcript, long session, provider fail, quota fail, repeated flush. [ ] Karar/hata/açık iş doğru çıkarıldı mı? [ ] Source citation zinciri korunuyor mu?
- [ ] API vs CLI vs local, mümkünse aynı görev maliyeti/latency/quality.
- **Kabul:** Capture coverage ve false-memory sayıları raporlu; kalite düşüşü olan model/config varsayılan yapılmaz.

#### B6-004 — Temporal/graph ve conflict değerlendirmesi (P0)
- [ ] Çoklu tarih, backdated import, `valid_from`/`recorded_at`, supersession, farklı proje kapsamı, bilgi sahibi değişimi.
- [ ] Graph açık/kapalı iş akışı, maliyet ve exactness karşılaştırması.
- **Kabul:** Kalan temporal hatalar tek tek kategorize; B5 Time Machine/Conflict sürümleri regression görür.

#### B6-005 — Retrieval kalite ve latency optimizasyonu (P0)
- [ ] FTS/semantik/hybrid/graph karşılaştır, chunk size, rerank, relevance threshold, warm model / on-demand process.
- [ ] Başlık, uzun paragraf, kod, Türkçe, yanlış proje, eski karar sorguları.
- [ ] Ölçümler P50/P95 ve RAM; yalnız hızlı diye relevance kaybı olan optimizasyon reddedilir.
- **Kabul:** Önceki release baseline'ına göre göreve bağlı kazanım kanıtı ve düşük-risk fallback.

#### B6-006 — Token/context/maliyet A/B testi (P0)
- [ ] Hafızasız vs tüm not vs 600/120/60 token budget vs adaptif. [ ] Task accuracy ve tekrar sorgu maliyeti; total provider tokens ve USD/TRY dönüşümü varsa kur kaynağı/tarihi.
- [ ] Token 'tasarrufu' yalnız prompt input değil oturum toplamı üzerinden raporlanır.
- **Kabul:** Net kazanç metriği ve tradeoff; tek bir sentetik prompt'tan pazarlama iddiası yapılmaz.

#### B6-007 — Cross-agent gerçek eylem benchmark (P0)
- [ ] Claude→Codex, Codex→Gemini vb. desteklenen istemciler. [ ] Bir önceki hatadan kaçınma, yeni API kararı uygulama, gerçek kod/test görevi.
- [ ] Agent sürümü, tool permissions ve manual intervention oranı kayıtlı.
- **Kabul:** Sadece devir paketi okundu değil; bitirilen gerçek görev, kaynak ve doğruluk raporu var.

#### B6-008 — Privacy Firewall & memory poisoning red team (P0)
- [ ] Harici belge→memory write→future recall→agent action→repair senaryoları. [ ] Bilinçli izinsiz data egress, model key sızması, UI/CLI bypass, graph traversal yetkisi.
- [ ] Memory purge sonrasında geri çağırma/Time Machine/backup/export sızıntı kontrolü; sistemin kendi kullanıcı backup sözleşmesi ile uyumlu retention.
- **Kabul:** Kritik sızıntı P0=0; bulunan her hata regresyon fixture'ına çevrilir.

#### B6-009 — Evidence Chain ve false certainty değerlendirmesi (P0)
- [ ] Hash kayıp, git history değişmiş, iki farklı kaynak, çok eski transcript; 'verified' yanlış işaretleme oranı.
- [ ] Kullanıcı doğru kaynağı kaç tıklamada buluyor; false-confidence UX testi.
- **Kabul:** Provenance ve explanation metrikleri raporlu; bilginin güveni kanıt olmadığında açık uyarı.

#### B6-010 — Simulator/Replay/Impact/Time Machine tutarlılığı (P1)
- [ ] Dry-run/real context eşleşmesi; as-of doğru; impact false positive; no-mutating guard.
- [ ] Yeniden indeksleme/taşıma sonrası replay snapshot idempotency.
- **Kabul:** Simülasyon ve gerçek retrieval ayrılmasının sınırları açıklanmış; yanlış as-of ve izinsiz side effect yok.

#### B6-011 — Skills Laboratory test-time öğrenme kalitesi (P1)
- [ ] Tekrarlı işe yarayan prosedür, yanlış skill, saldırgan talimat, şema değişiminden etkilenme.
- [ ] Skill on/off aynı coding görevinde deney; otomatik etkinleştirme yok.
- **Kabul:** Skill faydası/yanlış öneri metriği var; release öncesi güvenlik incelemesi geçerli.

#### B6-012 — Desktop UX, erişilebilirlik ve gerçek kullanıcı pilotu (P1)
- [ ] Gönüllü kullanıcılarla onboarding, ilk agent bağlama, hafıza arama, kaynak onayı, geri yükleme, devir. [ ] Zaman, başarı, hatalı tıklama, açıklanabilirlik ve gizlilik algısı.
- [ ] Klavye, ekran okuyucu, kontrast, yoğun veri ve ekran DPI testleri.
- **Kabul:** Kullanıcılarla gerçekten yapılan test sayısı açık; kritik kullanılabilirlik engeli kapanmış.

#### B6-013 — Çapraz-OS ve büyük veri dayanıklılığı (P0/P1)
- [ ] Windows, macOS, Linux, WSL: gerçek CI/runner veya fiziksel test. [ ] 10k/100k not sentetik ölçümü uygun donanımda. [ ] Crash, disk dolu, backup, restore, concurrent writers.
- [ ] İlk kurulum süresi/paket boyutu/RAM/CPU/başlatma süresi raporu.
- **Kabul:** Desteklenen platform tanımı kanıta eşit; performans darboğazları dosyalanmış.

#### B6-014 — Rakiplerle gerçek koşul parity/performans kıyası (P1)
- [ ] C01–C17 arasında kurulabilir ve lisans/izin açısından ölçülebilir örneklem seç. [ ] Aynı dataset/model ve izin limiti veya eşitlenemeyen farkların açık notu.
- [ ] 'Dokümanda var', 'kurduk', 'aynı görevde denedik' seviyelerini ayrı tut.
- **Kabul:** Rakip karşılaştırmaları aynı koşul olmadan sayısal üstünlük iddiası yapmıyor.

#### B6-015 — Evidence Report / optimizasyon freeze kararı (P0)
- [ ] Her kritik feature için: kaynak, deney, önce-sonra, repeat, limits, commit, donanım, model, test type, selected config.
- [ ] Beta.6 sonunda bütün benchmarkların güvenilir hash/sürüm kayıtları.
- [ ] Son optimizasyonları feature flag veya güvenli fallback ile dondur; beta.7 sadece kritik düzeltme.
- **Kabul:** Bir V1.0 özellik iddiasından Evidence Report'taki ilgili sonuca gidilebilir; açıklanamayan P0/P1 risk yok.

### G.4. Önerilen kalite hedefleri — gerçek baseline ile kalibre edilecek

| Gösterge | İlk hedef önerisi | Not |
|---|---|---|
| Idempotent capture | Aynı event için 0 çift kayıt | Deterministik fixture |
| Kasa veri bütünlüğü | Test edilen crash/migration/uninstall'da 0 kayıp | Mutlak tüm olasılıklar garanti değil |
| Yetkisiz yazma / egress | P0 senaryolarında 0 başarılı atlama | Red-team test kapsamı belgeli |
| Sentetik 50 soruluk regresyon | Beta.2 referans skorundan açıklanamayan düşüş 0 | 94% FTS ölçümünü karıştırma, yeni fixture farklı olabilir |
| Temporal karar | Eski kararı güncel sanma kritik senaryolarında 0 | Kapsam/dataset tanımlanmalı |
| Cross-agent | İlan edilmiş tam destek için gerçek test zorunlu | 'Connected' ile ayrı |
| Search | Recall@5/MRR düşmüyor, p95 izleniyor | Donanım ve semantik mod eşitlenmeli |
| Token optimizasyonu | Aynı görev kalitesinde toplam token azalması | Önce ölç, sonra sayısal hedef |
| GUI güvenilirliği | Kullanıcı senaryolarında bloklayıcı hata 0 | Pilot kapsamı açık |
| Bilinen P0/P1 release bug | 0 açık | Düşük öncelik bilinen kusur belgeli olabilir |

---

## H. BETA.7 — FEATURE FREEZE, BUG FIX VE RELEASE HARDENING

### H.1. Donma kuralları
- [ ] Yeni büyük ürün yeteneği/deneysel endpoint eklenmez. B4/B5 kapsamı beta.7'den önce tamamlandıysa bugfix süreci başlar; tamamlanmadıysa beta.7'e geçilmez.
- [ ] İstisna: Güvenlik, veri koruma veya platform desteğini gerçeğe uygun hale getirmek için zorunlu değişiklik; ADR/PR/test/rollback.
- [ ] Kullanıcı deneyimindeki engelleyici kusurlar düzeltilir; dekoratif yeniden tasarım beta.7'de büyük risk oluşturuyorsa ertelenir.
- [ ] Her bug → doğrulanan tekrar üretme senaryosu → regression test → küçük düzeltme → canary/release candidate.

### H.2. Hata sınıflandırma ve yayın blokları

| Derece | Örnek | Yayın kararı |
|---|---|---|
| P0 / Critical | Kasa silme, secret sızması, yetki bypass, yetkisiz provider çağrısı, imzalı update tamper | **Mutlak bloklayıcı**, açık 0 |
| P1 / High | Doğrulanmış kararı sessiz yanlış güncelleme, destekli agent gerçek bağlantısının bozulması, güvenli rollback çalışmaması | **Mutlak bloklayıcı**, açık 0 |
| P2 / Medium | Belirli filtre/ekran, az kullanılan opsiyon; açık workaround | Karar kayıtlı ve kullanıcı bilgilendirilmişse kabul edilebilir |
| P3 / Low | Kozmetik hizalama/animasyon/ikincil metin | Belgelenip sonraki yama sürümüne taşınabilir |

### H.3. Beta.7 görevleri

#### B7-001 — Frozen scope & defect triage (P0)
- [ ] Açık issue'ları severity, affected version, reproduction, data-loss risk ve owner ile triage et.
- [ ] 10 beta.5 feature ve parity registry'nin eksiği yok; yeni feature PR'ı kabul etmeme.
- **Kabul:** `Known Issues` ve P0/P1 sayacı gerçek.

#### B7-002 — Migration, backup, downgrade ve recovery matrix (P0)
- [ ] Beta.1→beta.2→beta.3→beta.4→beta.5→beta.7 fixture ve desteklenen doğrudan yükseltmeler. [ ] Mevcut `installation/migrate.py` `STEPS` tablosu gerçek şema değişimlerine göre. [ ] Downgrade açıkça desteklenmiyorsa bozucu işlem yerine açık uyarı.
- [ ] Onarım/kaldırma/reinstall, yarım kalan kurulum, disk dolu, anlık güç kaybı, kilitli dosya, bulut-senkron klasör, symlink.
- **Kabul:** Kasa veri kaybı yok, rollback testli, eski sürümlerden geçiş açık ve kaynaklı.

#### B7-003 — Desktop+Python sidecar crash and concurrency (P0)
- [ ] Tauri UI crash, sidecar timeout, iki eşzamanlı UI, iki agent MCP request'i, Windows shutdown, güncelleme sırasında agent aktif.
- [ ] Headless CLI/MCP gereksinimi tekrar. [ ] Process tree cleanup.
- **Kabul:** Yetkisiz yazma/bozuk state yok, çalışan agent ve kasa korunuyor.

#### B7-004 — Security/privacy penetration tests (P0)
- [ ] Tarayıcı/Markdown prompt injection, kötü niyetli PDF, SSRF, cross-vault path, user-approved note spoofing, policy bypass, key redaction, updater tamper.
- [ ] Tüm bulguları test fixture'ı + severity ile kaydet; 0 açık P0/P1.
- **Kabul:** Belirlenen saldırı ve regresyon setlerinde kritik sızıntı/izinsiz değişiklik yok.

#### B7-005 — Agent/providers regression matrix (P0)
- [ ] Tam destek ilan edilen her AI istemcisi için gerçek başlatma→capture→flush→recall→kapanış ve çapraz-agent deney. [ ] Ücretli model yalnız opt-in ve gerçek anahtarla. [ ] Provider quota/offline hata mesajları.
- **Kabul:** İlan edilen destek düzeyi gerçek kanıtla örtüşüyor; başarısız sağlayıcı bilgi kaybı üretmiyor.

#### B7-006 — UI QA ve accessibility (P1)
- [ ] Onboarding, Review, Graph, Replay, Time Machine, Skills Lab, izin diyaloğu, backup/restore; klavye, focus, contrast, reduced-motion, DPI, tema ve locale.
- [ ] Büyük listeler, empty/error states, 20+ aksiyonlu smoke testi ve görsel regresyon.
- **Kabul:** Bloklayıcı UX kusuru yok; kritik işlemler ekran okuyucu/klavyeyle yapılabilir.

#### B7-007 — Performans/stability soak (P1)
- [ ] Büyük sentetik kasa, 24–72 saat **önerilen** açık kalma deneyi; gerçek uygulama cihazı sınırlarına göre süre ayarla. [ ] Bellek sızıntısı, CPU, indeks artımı, graph rebuild, scheduler ve startup cold/warm.
- [ ] Semantik sağlayıcısı olmayan makinelerde FTS fallback.
- **Kabul:** P95/CPU/RAM performans regressions açıklanır, kritik donma/kasa kilidi yok.

#### B7-008 — Paketleme, imzalama, updater ve lisans (P0)
- [ ] Installer/sidecar hash, dağıtım metadata, update manifest, imza/sertifika durumu. [ ] Authenticode için sertifika varsa imzala; yoksa imzasız ibaresi ve riskleri belgeli. [ ] macOS notarization/Windows SmartScreen ancak gerçekten yapılınca ilan et.
- [ ] Açık kaynak ve üçüncü taraf parser/component/model lisansları denetimi; tersine mühendislikle kopya özellik implementasyonu yapma, davranıştan yeni tasarım çıkar.
- **Kabul:** Paket içeriği ve sürümü doğrulanabilir; yanlış imzalı/sertifikalı iddia yok.

#### B7-009 — Docs, support ve ürün iddialarının kanıtlanması (P0)
- [ ] README, Features, Release Notes, Privacy, Security, Terms varsa; agent destek tablosu, ücret/secret, offline/online, registry ve Evidence Report.
- [ ] 'Rakiplerden daha iyi' iddiası yalnız ölçüldüyse kullanılır. [ ] Kullanıcı destek ve debug için redacted diagnostic export.
- **Kabul:** Her kritik özellik ilanı test ve kaynakla tutarlı.

#### B7-010 — Beta.7 yayın kararı (P0)
- [ ] P0/P1 0; test/build/migration/cross-agent/UI/security kapıları başarılı; kanıt raporu ve bilinen P2/P3 listesi mevcut.
- [ ] Beta.7'de yeni feature istenirse sürüm kapısı geri açılmaz; yeni plan/sürüm kararı alınır.
- **Kabul:** İmzalı veya dürüstçe imzasız release channel ve dokümantasyon doğru.

### H.4. Beta.8+ / RC release flow

- [ ] Beta.7 sonrası yeni P0/P1 bulunursa küçük scope'lu **beta.8**, **beta.9** vb. düzeltme sürümleri; bütün ilgili regresyon seti tekrar.
- [ ] Özellikler dondurulmuşsa `1.0.0-rc.1`, `rc.2` gibi RC kullan; değişiklik listesi küçük tut, tam sürüm kapılarını her RC için tekrarla.
- [ ] RC yükseltme ve kararlı V1.0 yükseltmesi aynı veri/ayar sözleşmesiyle doğrulanmalı; RC'yi kullanmış kullanıcılar ceza görmemeli.
- [ ] P0/P1 açığı veya güvenilirlik regresyonu varsa V1.0 etiketi **atılmaz**.

---

## I. V1.0 — İLK RESMÎ SÜRÜMÜN ÖLÇÜLEBİLİR KABUL KRİTERLERİ

### I.1. Zorunlu ürün kapsamı
- [ ] Brain **Hub'sız** kurulur, başlar, çalışır, güncellenir ve kaldırılır; Python motoru pencereden bağımsız kullanılabilir.
- [ ] **Tauri 2 + React + TypeScript** Desktop ve Python Core nihai paketlenmiş sürümde çalışıyor; motor Rust'a taşınmak zorunda değil.
- [ ] Beta.4 registry kapsamındaki **tüm hedef çekirdek hafıza yetenekleri** uygulanmış, acceptance test ve gerçek örnek kanıtıyla işaretli. Diğer tüm rakip yetenekleri de değerlendirilmiş ve mimari kararları kayıtlı.
- [ ] Beta.5'te **10/10 onaylı farklılaştırıcı özellik** teknik, UX, güvenlik ve test acceptance'larından geçmiş.
- [ ] Kullanıcı Markdown kasası taşınabilir; `vault_uuid`, kaynak, doğrulama, tarih ve izin kayıtları doğru korunur.
- [ ] CLI/MCP/RPP, gösterilen UI'dan farklı davranmıyor; kritik yetkiler tek Python domain servisinde uygulanır.
- [ ] Desteklendiği ilan edilen bütün agent/OS/model kipleri gerçek doğrulama raporuna sahip; doğrulanmayanlar deneysel sınıfında veya destek dışı.

### I.2. Geliştirme/kalite kapıları
- [ ] Full unit/integration/component/e2e/UI smoke ve test raporu PASS.
- [ ] Benchmarks aynı data hash/model/OS/commit ile yeniden üretilebilir.
- [ ] P0/P1 hata 0; açık P2/P3 gerekçeli, kullanıcıya açıklanmış.
- [ ] Kritik veri bütünlüğü ve mahremiyet fixture'larında 0 bilinen ihlal.
- [ ] Kasa restore, kurulum/onarma/kaldırma/upgrade/rollback/downgrade davranışı belgeli ve testli.
- [ ] Beta.6 Evidence Report her kritik özellik için en az bir test/deney bağlantısı içeriyor.
- [ ] CPU/RAM/cold-start/p95 latency ve token maliyeti karşılaştırmaları raporlu.
- [ ] Uygulama erişilebilir; kritik UI akışları klavye ve ekran okuyucuyla kullanılabilir.
- [ ] Platform imzalama/uyarı/sınır açıklamaları gerçeğe uygun; hiçbir işlev 'kanıtlandı' denip sadece mock'ta bırakılmamış.
- [ ] Tüm README, ROADMAP, ROADMAP-EXECUTION, RELEASE-GATE, CHANGELOG ve versiyonlar çelişmiyor.

### I.3. İstenen kanıt makbuzu şeması (öneri)

```json
{
  "task_id": "B5-04",
  "version": "0.1.0-beta.5",
  "commit": "<sha>",
  "status": "REAL-VERIFIED",
  "scope": "Claude Code -> Codex, Windows x64, fixture-v3",
  "commands": ["<actual executed command>"],
  "tests": {"passed": 0, "failed": 0, "skipped": 0},
  "dataset_sha256": "<hash>",
  "model_and_provider": "<exact versions>",
  "security": {"cross_scope_leak": false, "sensitive_output_leak": false},
  "metrics": {"task_success_rate": null, "tokens": null, "p95_ms": null},
  "limitations": ["<known gap>"],
  "artifacts": ["<json report path>", "<redacted log path>"],
  "reviewed_at": "<iso-8601 timestamp>"
}
```

> Bu JSON **şema örneği**; testlerin yapıldığı veya başarı oranı ölçüldüğü anlamına gelmez. Gerçek rapora boş/dummy metrikler başarı diye yazılmamalıdır.

### I.4. Kamuya açık konumlandırma ve savunulabilir iddia

**Önerilen ürün cümlesi:** *Respected Brain, farklı AI coding araçları arasında kullanıcıya ait, kaynaklı, güncel ve denetlenebilir hafızayı korur; ilgili bilgiyi doğru zamanda, kontrollü bağlamla geri verir.*

- 'Rakiplerin bütün hafıza özellikleri' ancak sabitlenmiş registry kapsamı ve işlevsel parity tablolarıyla açıklandığında kullanılabilir.
- 'En hızlı/en doğru/en güvenli' gibi evrensel iddialar kapsamlı bağımsız kanıt olmadan kullanılamaz.
- Yeni 10 özelliğin çoğunda benzer fikirler başka ürünlerde bulunabilir; farklılığımızı **somut kullanıcı deneyimi ve kanıtlı sonuç** üzerinden konumlandır.

---

## J. HER GÖREV/PR İÇİN ORTAK DEFINITION OF DONE

1. İşin kullanıcı sorunu ve sınırı açık.
2. Önce mevcut kodda aynı işlev var mı kontrol edildi; var ise gereksiz yeniden yazılmadı.
3. Bağımlılıkları, etkilenen modül/API, migration/feature flag/fallback ve rollback yazıldı.
4. Python domain / Tauri bridge / React UI / MCP/CLI/RPP değişiklikleri uygun alanlarına dağıtıldı.
5. Pozitif, negatif, regresyon, crash/kurtarma, izin, gizlilik ve çoklu-agent senaryoları etkiye göre eklendi.
6. Kullanıcı kasasında **sessiz** destructive işlem yok; audit/dry-run/approval yerinde.
7. Yeni provider/API için ücret ve veri çıkışı açık.
8. Gerektiğinde arayüz: boş, bekleme, başarısızlık, erişilebilirlik, error copy, progress, cancel/rollback.
9. Testler izole geçici köklerde, ham özel kullanıcı verisi olmadan çalıştırıldı.
10. Kod, test, tasarım, docs aynı PR'da; ürün sözleşmesi etkilenirse conformance güncellendi.
11. Benchmarks önce-sonra, gerçek model/fixture ve 'unavailable' farkları dürüst raporlandı.
12. Kanıt kaydı/commit/CI linki issue'ya bağlandı; `PLAN/IMPLEMENTED/VERIFIED` ayrımı korunuyor.
13. Her aşamada P0/P1 yeni hata bulunduğunda sonraki sürüme havale edilmeden gideriliyor.
14. Ürün sahibinin onayladığı beta.5 on özellikten hiçbiri dokümanda sessizce kaybolmuyor.

---

## K. BETA.2 → V1.0 BAĞIMLILIK VE GÖREV GÖRÜNÜMÜ

| Grup | Görev aralığı | Bağımlılık | Çıkış kanıtı |
|---|---|---|---|
| B2 — Mini Release Validation | B2-G00…G07 | Güncel beta.2 çalışma dalı | Beta.2 release gate ve gerçek test raporu |
| B3 — Independent Desktop | B3-001…015 | Beta.2 release | Tauri installer + Python sidecar + Hub'sız smoke + migration |
| B4 — Parity Research/Implementation | B4-001…025 | Beta.3 IPC, vault model | Registry + her hedef capability'nin acceptance & UI kanıtı |
| B5 — 10 özellik | B5-01…13 | Beta.4 source/graph/security/retrieval | 10/10 feature QA + gerçek iş akışı demosu |
| B6 — Research & Optimization | B6-001…015 | Beta.5 feature complete | Evidence Report + benchmark+pilot+security |
| B7 — Stabilization | B7-001…010 | Beta.6 optimize edilmiş özellikler | P0/P1 0, full test/migration/package gate |
| RC / V1.0 | H.4 + I | Beta.7 kapıları | Son signed/unsigned dürüst release, migrasyon ve kanıt |

### K.1. Önceden mevcut BR görevleri ile eşleştirme (duplicate iş önlemi)

- `BR-001/003`: B2-G02 ve B6 benchmark tabanı; yeniden harness yazma yok.
- `BR-002/004/005/006`: B2-G03/G04, B6-003/007, B7-005.
- `BR-007/008/009`: B4-003/005/006, B5-01/03/06/07.
- `BR-010/011/012`: B2-G02, B4-007/009, B5-05, B6-005/006.
- `BR-013`: B2-G05, B4-024, B5-02, B6-008, B7-004.
- `BR-014/015`: B2-G06/G07, B3-007/015, B7-008/010.
- `BR-016/017/018`: B2-G04, B3-012, B4-008/013/014; kod var, gerçek test/UX ve genişleme farkı takip edilir.
- `BR-019`: B3-015, B6-013, B7-008; platformu gerçek test olmadan desteklenmiş ilan etme.
- `BR-020`: B4-011/016/017, B5-10; kalan ileri öğeler registry ile ayrıştırılır.

### K.2. Tahmini risk ve iş büyüklüğü (süre garantisi değildir)

- **En yüksek risk:** B3 Python sidecar+Hub migration; B4 graph schema+güncellik; B5 Privacy Firewall/Conflict/Time Machine; B6 gerçek-world eval; B7 çoklu platform imza/updater.
- **XL işler** tek PR değil, küçük reversible alt PR'lara bölünür. Örneğin B5-02: policy schema→Python guard→MCP guard→provider egress→UI→end-to-end.
- **Geliştirme darboğazı:** Kullanıcıya erişim, gerçek platform makineleri ve gerçek model API anahtarları yoksa `real-verified` kapısı tamamlanamaz; eksikliği saklama.
- **Zorunlu kalite gecikmesi:** Testler yavaşlarsa ürün talebinden test silme değil, testleri hızlı unit / orta integration / gerçek smoke katmanlarına ayırma.

---

## L. KAYNAKLAR VE TARİHLER — `docs/kaynak` SİLİNDİKTEN SONRA KORUNACAK BAĞLANTILAR

### L.1. Respected Brain kaynakları
- https://github.com/respected0/respected-brain
- https://github.com/respected0/respected-brain/blob/main/docs/ROADMAP.md
- https://github.com/respected0/respected-brain/blob/main/docs/ROADMAP-EXECUTION.md
- https://github.com/respected0/respected-brain/blob/main/docs/ARCHITECTURE.md
- https://github.com/respected0/respected-brain/blob/main/docs/RELEASE-GATE.md
- https://github.com/respected0/respected-brain/releases

### L.2. Masaüstü / güvenlik teknik kaynakları
- Tauri 2 sidecar: https://v2.tauri.app/develop/sidecar/
- Tauri 2 capability/permissions: https://v2.tauri.app/security/capabilities/
- Python packaging ve mevcut repo `packaging/build_dist.py`: repo source of truth.

### L.3. Rakip kaynakları
- Rakip tam liste ve URL'leri: **E.2**.
- 135 araçlık kataloğun önemli kayıtlarının dosya bağımsız bağlantıları: **E.3**.
- Araştırmalar, DOI/resmî makale ve benchmark URL'leri: **G.1**.

### L.4. Lisans ve bağımsızlık uyarısı
- Rakiplerin özellik davranışını örnek alıp yeni uygulama tasarlamak ile rakibin kodunu/lisanslı materyalini kopyalamak farklıdır. Her üçüncü taraf kod/model/asset için açık lisans ve attribution denetimi şart.
- Üçüncü taraf benchmark iddiaları farklı modeller/veri hazırlıkları/agent harness'leriyle üretilebilir. **Brain'in üstünlüğünü ancak aynı koşul testleri ve açık protokol gösterebilir.**
- Zamanla değişen ürünlerde 5 Kasım 2026 tespiti güncel kalmayacaktır. Beta.4 başlangıcı ve beta.6 benchmark tarihi için kayıtlı yeni snapshot alın.

---
## M. Kaynak aktarım kaydı (SOURCE-TO-ROADMAP-MAP)

Bu plan `docs/kaynak/` altındaki geçici kaynak belgeden bu dosyaya aktarıldı. Aşağıdaki tablo her görev kimliğinin bu dosyadaki başlık satırını gösterir. A–L ve N bölümleri kaynakla aynı başlıklarla bu dosyadadır; kaynaktaki aktarım talimatı (eski M) yerine bu kayıt konmuştur.

Coverage: 8 B2 + 15 B3 + 25 B4 + 13 B5 + 15 B6 + 10 B7 = **86** görev; beta.8+/RC akışı H.4, V1.0 kriterleri I, BR eşlemesi K.1, rakipler E.2 (C01–C17 + Mem0/Letta/Graphiti), 135 araç kaydı E.3, araştırmalar G.1 (R01–R12).

| Görev | Bu dosyada (satır) | Bölüm |
|---|---|---|
| B2-G00 | 99 | C |
| B2-G01 | 107 | C |
| B2-G02 | 115 | C |
| B2-G03 | 123 | C |
| B2-G04 | 130 | C |
| B2-G05 | 137 | C |
| B2-G06 | 145 | C |
| B2-G07 | 154 | C |
| B3-001 | 201 | D.3 |
| B3-002 | 208 | D.3 |
| B3-003 | 214 | D.3 |
| B3-004 | 220 | D.3 |
| B3-005 | 226 | D.3 |
| B3-006 | 232 | D.3 |
| B3-007 | 238 | D.3 |
| B3-008 | 244 | D.3 |
| B3-009 | 250 | D.3 |
| B3-010 | 256 | D.3 |
| B3-011 | 262 | D.3 |
| B3-012 | 268 | D.3 |
| B3-013 | 274 | D.3 |
| B3-014 | 280 | D.3 |
| B3-015 | 286 | D.3 |
| B4-001 | 388 | E.5 |
| B4-002 | 394 | E.5 |
| B4-003 | 400 | E.5 |
| B4-004 | 406 | E.5 |
| B4-005 | 412 | E.5 |
| B4-006 | 418 | E.5 |
| B4-007 | 424 | E.5 |
| B4-008 | 430 | E.5 |
| B4-009 | 436 | E.5 |
| B4-010 | 442 | E.5 |
| B4-011 | 448 | E.5 |
| B4-012 | 454 | E.5 |
| B4-013 | 460 | E.5 |
| B4-014 | 466 | E.5 |
| B4-015 | 472 | E.5 |
| B4-016 | 478 | E.5 |
| B4-017 | 484 | E.5 |
| B4-018 | 490 | E.5 |
| B4-019 | 496 | E.5 |
| B4-020 | 502 | E.5 |
| B4-021 | 508 | E.5 |
| B4-022 | 514 | E.5 |
| B4-023 | 520 | E.5 |
| B4-024 | 526 | E.5 |
| B4-025 | 532 | E.5 |
| B5-01 | 554 | F / F.1 |
| B5-02 | 566 | F / F.1 |
| B5-03 | 578 | F / F.1 |
| B5-04 | 590 | F / F.1 |
| B5-05 | 602 | F / F.1 |
| B5-06 | 614 | F / F.1 |
| B5-07 | 626 | F / F.1 |
| B5-08 | 638 | F / F.1 |
| B5-09 | 650 | F / F.1 |
| B5-10 | 662 | F / F.1 |
| B5-11 | 676 | F / F.1 |
| B5-12 | 682 | F / F.1 |
| B5-13 | 688 | F / F.1 |
| B6-001 | 745 | G.3 |
| B6-002 | 751 | G.3 |
| B6-003 | 757 | G.3 |
| B6-004 | 762 | G.3 |
| B6-005 | 767 | G.3 |
| B6-006 | 773 | G.3 |
| B6-007 | 778 | G.3 |
| B6-008 | 783 | G.3 |
| B6-009 | 788 | G.3 |
| B6-010 | 793 | G.3 |
| B6-011 | 798 | G.3 |
| B6-012 | 803 | G.3 |
| B6-013 | 808 | G.3 |
| B6-014 | 813 | G.3 |
| B6-015 | 818 | G.3 |
| B7-001 | 860 | H.3 |
| B7-002 | 865 | H.3 |
| B7-003 | 870 | H.3 |
| B7-004 | 875 | H.3 |
| B7-005 | 880 | H.3 |
| B7-006 | 884 | H.3 |
| B7-007 | 889 | H.3 |
| B7-008 | 894 | H.3 |
| B7-009 | 899 | H.3 |
| B7-010 | 904 | H.3 |

---

---

## N. SON ÜRÜN İLKESİ

**Respected Brain bir başka Orchestrator, bir genel CRM veya bir MCP mağazası olmayacak.** Bir AI coding aracının güvenilir biçimde öğrendiği bilgi, başka bir AI aracına geçtiğimizde kaybolmayacak; kaynağı ve zamanı bilinecek; yanlış/eskimişse düzeltilecek; ilgili bağlam düşük gereksiz maliyetle geri verilecek. Bağımsız Tauri masaüstü uygulaması bu hafızayı kullanıcıya anlaşılır ve kontrol edilebilir hale getirecek. Beta.4 rakiplerin bütün ilan edilmiş özelliklerini inceleyecek, hafızayla ilgili hedef yeteneklerini uygulayacak; beta.5 kabul edilen **10/10** yeniliği getirecek; beta.6 bilimsel/gerçek kullanım kanıtlarını toplayacak; beta.7+ kararlılığı sağlayacak; V1.0 bütün bunların doğrulanmış ürünü olacak.
