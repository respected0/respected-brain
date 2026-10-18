# Ürün çıkarımı uygulama ve kanıtı — 2026-10-09

scope: source-extraction; confidence: tested-with-listed-limits

## Teslim sonucu

Stage A kaynak sınırları ve Stage B'nin ilk bağımsız motor yolu uygulandı.
Stage C için gerçek Tauri 2/React/TypeScript kaynak ve native IPC yazıldı;
TypeScript build geçti, **native desktop acceptance tamamlanmadı**. Stage D
silme/dağıtım ayrımı ve Stage E hardening kabulü tamamlanmadı.

Brain ürün/paket kaynağı 142/142 başlangıç atlası hash'iyle eşleşiyor. Canlı
uygulama/kasa, AI hook/MCP/router/settings yüzeyleri değiştirilmedi. Kaynak
depolar üzerinde Git komutu/commit yapılmadı. Motor ve mevcut atlas testlerinin
Git fixture işlemleri yalnız geçici test projelerindeydi. Yeni kardeşlerde `.git`
oluşturulmadı; kullanıcı Git yönetimini yapar. Global bağımlılık kurulmadı,
kalıcı background service eklenmedi, paralel ajan kullanılmadı.

## Oluşturulan kaynaklar ve çıkarılan kod

| Dizin | Dosyalar / sorumluluk |
| --- | --- |
| `../respected-orchestrator/` | pyproject, README, AGENTS, ignore, bağımsız tools/docs atlası |
| `../respected-orchestrator/src/respected_orchestrator/` | `context.py` bağımsız roots/state; `runner.py` görev oluşturma/çalıştırma/inspect/cancel/retry/check; `processes.py` deadline/streaming logs/Windows job/POSIX group; `__main__.py` private JSON; `__init__.py` ürün kimliği |
| `../respected-orchestrator/src/respected_orchestrator/antigravity_orchestrator.py` | Brain'den gerçek mevcut lane, overlay/baseline, brief, writer lock, provider classification, scope, acceptance, binary patch ve compatibility yardımcıları çıkarıldı. Bağımlılıklar independent context/process katmanına uyarlandı |
| `../respected-orchestrator/src/respected_orchestrator/resources/` | bypass=false policy; yeni bağımsız akışa uyarlanan kod-orkestrasyon skill'i |
| `../respected-orchestrator/tests/` | 26 korunmuş/uyarlanmış Antigravity testi ve 21 gerçek independent engine testi |
| `../respected-hub/` | package/package-lock, TypeScript config, index, README, AGENTS, ignore, tools/docs atlası |
| `../respected-hub/src/` | React ürün/görev/settings yüzeyi, tipli Tauri API, task JSON doğrulama ve stil |
| `../respected-hub/src-tauri/` | Cargo/build/config/capability, native Rust engine bridge, product discovery ve settings persistence |
| `../respected-hub/tests/` | 4 task form / pending-state testi |
| Brain `docs/decisions/PRODUCT_EXTRACTION.md` | Kullanıcının uygulama sırası, sınırlar ve kaldırma kapısı |
| Bu tarihli kayıt | Implementation, özellik sahipliği, 292 dosyalık başlangıç envanteri |
| Brain `tools/repository_map.py`, ilgili test | Git çalıştırmadan atlas keşfi; bağımsız ürün adıyla render. Normal Git CI davranışı korunur |

Her yeni kaynak dosyası ilgili ürünün `docs/repository_inventory.json` içinde
ayrı rol/amaç/ilişki taşır; tam dosya listeleri üretilen atlaslardadır. Yeni
ürünlerin developer aracı kopyaları bağımsızdır; ortak dördüncü depo yoktur.
node_modules, wheel/build/cache, kullanıcı verisi veya credential kaynak kopyası
değildir. Wheel `.local/archives/wheels/` içindedir.

## Şimdi kullanılabilen engine yolu

Hub native kabulü beklerken geliştirici private JSON girişinden task oluşturup
başlatabilir; README'de komut/request örneği var. Codex, Claude, Gemini,
Antigravity, Cursor discovery ve özel argv adaptörü vardır. Herhangi bir AI veya
kullanıcı task'ı hazırlayabilir; `master` metadata label'ı korunur.

Git projesi açık absolute path ve bounded ownership ile seçilir. Task root'u
proje/ürün kodundan ayrı DataRoot'tadır. Worker izole worktree'de çalışır; ana
proje otomatik değiştirilmez. Owned dirty tracked girdiler ve explicit seçilen
nonignored untracked girdiler baseline'a alınır. Read görevi dosya değiştirirse,
write görevi scope dışına taşarsa veya acceptance başarısızsa task başarısızdır.
Acceptance sonrasında scope yeniden kontrol edilir; yeni ignored dosyalar da
kapsam kontrolündedir. Binary patch kaynak baseline'ına göre üretilir.

Worker ve doğrulama deadline/iptal kullanır. Windows child suspended açılır,
kill-on-close job'a alınır ve sonra resume edilir. Live redacted log, queued /
running / completed / failed / timed_out / cancelled / interrupted status ve
patch inspect vardır. Pending durumu complete diye gösterilmez. Supervisor
çağırandan ayrılır ve caller kapanınca sürer. Windows supervisor ölünce worker
alt ağacı kapanır; stale writer lock inceleme için korunur.

Result/request/status HMAC ile bağlanır; `check` ayrıca patch SHA256, run sahibi,
başarılı test kanıtı ve güncel kaynak fingerprint/patch uyumunu doğrular.
Başarısız/stale/tampered sonuç kabul edilmez. Otomatik apply yoktur. Retry açık
eylemdir ve iki tekrar/üç toplam attempt sınırı vardır; auth/quota otomatik retry
döngüsü açmaz; aynı başarısız görevden yeni retry dalları açılarak budget sıfırlanamaz. Tam OS sandbox ve aynı kullanıcıya karşı key izolasyonu iddiası
yoktur; bu sınırlar README ve sahiplik kaydında açıktır.

## Gerçekte çalıştırılan doğrulama

| Kapı | Komut / yöntem | Sonuç |
| --- | --- | --- |
| RED independent task contract | İlk `test_engine.py` keşfi | Beklenen missing-module RED; daha sonra gerçek implementasyon |
| RED safety additions | bypass, live log, ignored scope vakaları | Beklenen eski davranış hataları görüldü ve shared code'da düzeltildi |
| Independent Orchestrator tam suite | `python -W error::ResourceWarning -m unittest discover -s tests -p 'test_*.py' -q` | **47/47 PASS**, 81.037 s, 0 skip |
| Private Hub JSON boundary ve ürün policy | JSON create/start/inspect/check/list round-trip + compatibility doctor defaults | Gerçek private subprocess yolu ve independent policy **PASS**; Rust IPC testi değildir |
| Native Windows lifecycle/process test kapsamı | Aynı suite: timeout descendants, supervisor crash, canlı cancel, caller-exit completion | Gerçek Python worker + alt süreçlerle PASS; canlı provider login testi değildir |
| Brain odaklı regressions | `python -m unittest tests.repository_map_test tests.foundation_memory_test tests.maps_test tests.mcp_and_features_test tests.briefing_schedule_test -q` | **77 vaka / 76 PASS / 1 koşullu skip**, 5.314 s |
| Brain kaynak/paket korunumu | Başlangıç atlası normalize-content SHA256 karşılaştırması | **142/142 eşit** |
| Yeni engine bağımsızlığı | Python AST import kontrolü + sadece yeni src ile bütün testler | **0 Brain import/dependency** |
| Wheel build | `python -m pip wheel . --no-deps --no-build-isolation --wheel-dir .local/archives/wheels` | Final `respected_orchestrator-0.1.0-py3-none-any.whl`; SHA256 `1eabbe198bb3fdbc1c82a26446660c01b84e58de42e28fd626a183927da552b3` |
| Final wheel kaynak/kurulu smoke | ZIP üyeleri kaynakla karşılaştırıldı; wheel geçici site'a çıkarılıp `python -I` ile task/write/check ve resource testi koştu | **8/8 byte eşleşmesi; 1/1 PASS**, 1.869 s; policy/skill dahil, 0 Brain import |
| Hub TS/frontend | `npm run build` | TypeScript + Vite PASS, 34 modül; final build 886 ms |
| Hub task contract | `npm test` | **4/4 PASS**; invalid JSON/scope/acceptance ve pending durumları |
| Native Tauri | `npm run tauri -- build --no-bundle` | **BLOCKED:** `cargo metadata ... program not found` |

Brain test çıktısındaki MAP_DRIFT satırı atlas drift regresyonunun beklenen RED
fixture'ıdır; suite hata değildir. Python 3.13 `PurePath.is_reserved` deprecated
uyarısı eski Brain kodundan gelir; extraction kapsamında değiştirilmedi.

Atlas `--filesystem-only` kapıları Brain 296, Orchestrator 17, Hub 22 açıklamalı
dosyada geçti; bu mod kaynak Git
işlemi yapmaz. Root ignore keşfi Git staged/nested-ignore semantiğiyle eşdeğer
diye sunulmaz. Normal CI modu değişmedi; push/CI çalıştırılmadı veya izlenmedi.

## Engel ve kesin sonraki görev

Windows host'ta PATH ve standart yerel konumlarda Rust/Cargo yok; Visual Studio
C++ build tools konumları da bulunmadı. Global kurulum kullanıcı sınırı nedeniyle
yapılmadı. Native Rust kodu derlenmedi, gerçek Hub window/IPC/settings/folder
picker round-trip kabulü yapılmadı. Web build bu native kabul yerine geçmez.

**Kesin sonraki görev:** kullanıcı tarafından sağlanan Rust/Cargo + Windows C++
toolchain ile `npm run tauri -- dev` ve `npm run tauri -- build --no-bundle`
çalıştır; geçici project/DataRoot seçerek task create/start/live logs/cancel /
completed-failed / stale-tamper-check ve Hub kapanışından sonra inspect akışını
native pencerede doğrula. Ardından explicit recovery/cleanup/apply karşılıklarını
ve Brain memory yönetim yüzeylerini tamamla. Ancak bu eşdeğerlik kapıları geçince
Brain orchestration dağıtımını ve eski dashboard'u kaldır.

Üretim ürün install/update/repair/removal, visual feature toggles ve integration
yönetimi uygulanmış değildir. RPP/SIL/finite Lifecycle Core, ownership, crash
recovery ve secure distribution hedefleri korunur. macOS/Linux, signing, gerçek
provider login/OS sandbox, tam Brain suite ve yeni CI bu turda doğrulanmadı.
Kalan işler ve ürün sahipleri [özellik koruma kaydında](FEATURE_PRESERVATION.md).
