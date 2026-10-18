# Özellik koruma ve ürün sahipliği — 2026-10-09

scope: source-extraction; confidence: code-inspected; release-acceptance: pending

Eksiksiz başlangıç dosya envanteri [BRAIN_BASELINE_INVENTORY.json](BRAIN_BASELINE_INVENTORY.json)
içinde korunur: 292 dosyanın rol/amaç/ilişkileri ve inceleme hash'leri. Güncel
değişiklikler [Brain atlasında](../../REPOSITORY_MAP.md), iki yeni ürünün bütün
dosyaları kendi atlaslarında açıklanır. Bu kayıt özellik silme izni değildir.
İstekte geçen ayrı pre-extraction audit / feature-preservation dosyaları mevcut
docs/decisions, docs/records ve .local'da bulunmadı; kullanıcıdan yolları istendi.
Tarihsel F1–F15 numaraları elde olmayan metinden yeniden uydurulmadı.

| Mevcut kaynak / özellik | Ürün sahibi | Bu aşamadaki koruma / taşıma |
| --- | --- | --- |
| `memory/` capture, transcript normalizasyonu, daily/session state, dedup, events, recall, graph, knowledge compiler | Brain | 11 kaynak kaydı yerinde korundu; kod değişmedi |
| Companion projeksiyonu ve vault-template Companion seed'leri | Brain | Memory/events ve immutable kaynaklar yerinde korundu |
| `briefing/` günlük compile/run-if-due | Brain | 2 kayıt ve scheduler bağları korundu |
| `search/` FTS5/BM25 indeks ve sorgu | Brain | 2 kayıt korundu |
| `integrations/` hooks, MCP, provider rendering, scheduler, global instruction/skill bağlantıları | Brain / Hub yönetimi | 13 kaynak kaydı korundu; mevcut dış provider ayarı değiştirilmedi |
| `providers/` memory model router/runner | Brain | 2 kayıt korundu; yeni engine bunları import etmez |
| `maintenance/` ingestion, not lint/repair/merge, URL okuyucu, Restic, Git backup ve secret guard | Brain | 14 kayıt korundu |
| `vault/` UUID registry, selection, maps | Brain | 3 kayıt korundu; Orchestrator vault gerektirmez |
| `core/`, bootstrap, launcher, CLI, root/resource/coordination sözleşmeleri | Brain | Brain bağlamı korunur; engine kendi bağımsız context'ini kullanır |
| `resources/` defaults, instructions, 10 skills, provider şablonları, vault seed'leri | Brain / hedefe özgü kaynaklar | 55 kaynak kaydı korunur; kod-orkestrasyon skill'i yeni ürüne uyarlanır. Araştırma skill'i Brain maintenance bağı nedeniyle yerinde kalır |
| `orchestration/runner.py` generic master/worker, CLI discovery, isolated worktree, task spec, logs, acceptance, binary patch, inspect/apply/reject/cleanup | Orchestrator | Generic provider komutları ve izolasyon akışı bağımsız signed task lifecycle'a taşındı. Task üreticisi kullanıcı veya herhangi bir AI olabilir. Manual apply/reject/cleanup eşdeğerliği henüz tamamlanmadı; eski Brain kodu korunur |
| `orchestration/antigravity_orchestrator.py` policy, lane, bounded brief, dirty/untracked overlay, baseline, writer lock, circuit breaker, scope, acceptance, patch check, detached runs | Orchestrator | Mevcut kod çıkarıldı; Brain context/vault/lease bağı kaldırıldı. Yeni default bypass false, timeout ve process-tree kontrolleri var; 26 eski test uyarlanarak korunur |
| `gateway/` ve `resources/gateway/web/` dashboard/memory ve orchestration UI | Hub | Tauri native kaynak ve gerçek JSON engine köprüsü yazıldı. Native build engelli; bütün eski dashboard sorumlulukları henüz eşdeğer değil, kaldırılmadı |
| `installation/` setup/update/repair/uninstall/migration, WAL/recovery, ownership, provenance, OS backend | Hub / gelecekte finite Lifecycle Core | Mevcut 16 Brain modülü korunur. Yeni Hub üretim lifecycle desteği iddia etmez |
| `packaging/`, kaynak bütünlük araçları, platform scripts ve tüm mevcut tests/docs | İlgili ürün / Brain geçiş kaydı | Kopyalanmayan Brain kayıtları yerinde kalır; yeni ürünler ayrı manifest/atlas/test taşır |

**Ayrımın kapanış koşulu:** taşıma, eski özelliklerin dağıtımdan kaldırılması
değildir. Hub native kabulü, memory yönetim yüzeyleri ve engine apply/cleanup
karşılıkları doğrulanınca Stage D için ayrı kaynak değişikliği yapılır. Brain
ürün/kaynak dosyaları bu turdaki başlangıç atlasıyla 142/142 hash eşleşti.

## Bağımsız hardening sahipleri

| Kalan konu | Sahip | Kesin sonraki iş / sınır |
| --- | --- | --- |
| Authenticode, gerçek attestation, yayın kabulü | Brain ve her yeni ürün | Her artifact için imza/provenance ve native gate; eski Brain kanıtı yeni ürün kabulü değildir |
| Canlı provider CLI sözleşmeleri, OS sandbox ve token/oturum kabulü | Orchestrator | Default approval koruyan Codex/Claude/Gemini/Antigravity/Cursor kabul matrisi; custom test gerçek login testi değildir |
| Scope yalnız sonradan denetleniyor; aynı kullanıcı erişimi HMAC key'i okuyabilir | Orchestrator | OS containment ve worker erişim sınırı; local evidence signature adversarial sandbox değildir |
| Stale lock, lane temizliği ve crash recovery | Orchestrator | Sahiplik/kimlik kanıtıyla explicit recover/cleanup; mevcut stale lock fail-closed korunur |
| Patch apply / reject / baseline freshness yarışı | Orchestrator | Signed evidence ve bounded project writer lock altında explicit inceleme/apply; otomatik apply yok |
| Worker concurrency / manual worker mode | Orchestrator | Mevcut independent task root'unda tek aktif görev; manuel user worktree edit/finish ve bounded scheduling henüz yok |
| Native Hub IPC + folder picker ve settings acceptance | Hub | Rust/Cargo + C++ araçları sağlandıktan sonra gerçek Tauri pencere testi |
| Feature toggles, product install/update/repair/removal ve integration yönetimi | Hub | Brain mevcut ownership/WAL davranışını koruyan görsel lifecycle uygulaması |
| RPP, SIL, finite Lifecycle Core, compatibility adapters ve secure distribution | Hub / ilgili engine | Sözleşme hedefleri korunur; dördüncü ortak repo oluşturulmaz |
| macOS/Linux Windows dışı crash/timeout/native acceptance ve code signing | İlgili ürün | Fiziksel platform test ve imzalı release; framework hedefleyebilmesi destek iddiası değildir |

Bu tablo tarihsel denetim maddelerini yeniden numaralandırmaz. F1–F15 referansı
geldiğinde kayıp metinle bire bir eşleştirme yapılmalı; extraction'ı tekrar audit
döngüsüne çevirip her geçmiş bulguyu kapatmaya çalışılmamalı.
