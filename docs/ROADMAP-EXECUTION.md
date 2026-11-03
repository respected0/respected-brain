# Respected Brain — Yürütme Yol Haritası ve Kanıt Günlüğü

Kaynak: Roadmap v2 (28 Ekim 2026). Bu dosya görev sırasını ve her görevin kanıtını tutar.
Kural: Bir görev, kanıtı bu dosyaya işlenmeden tamamlanmış sayılmaz; kanıt yoksa sonraki göreve geçilmez.

## Ürün hedefi

AI aracının öğrendiği doğru bilgi; araç veya oturum değiştiğinde kaybolmamalı, güvenilir biçimde bulunmalı, güncellenmeli ve geri getirilmelidir.

Ana süreç: **AL → SAKLA → GÜNCELLE → GERİ VER**

## Değişmeyen mimari sınırlar

- Markdown kasası kullanıcıya aittir; kaldırma/onarım/güncelleme onu silmez.
- AI üretimi bilgi otomatik olarak doğrulanmış gerçek veya kullanıcı kuralı sayılmaz.
- Ham sohbetlerin kalıcı arşivi varsayılan olarak kapalıdır.
- Brain, Orchestrator'ın görev dağıtma sorumluluğunu üstlenmez.
- Her mesajda tüm hafıza modele gönderilmez.
- Yeni özellikler RPP izinlerini, kurulum sözleşmesini ve geriye dönük veri uyumluluğunu bozmaz.

## Yürütme sırası

1. BR-001 — Memory Evaluation Harness
2. BR-003 — Mevcut sürüm baseline raporu
3. BR-002 — Memory Pipeline Diagnostics
4. BR-004 — Gerçek agent entegrasyon matrisi
5. BR-005 — Yakalama dayanıklılığı ve idempotency
6. BR-006 — Oturum özetleme doğruluğu
7. BR-007 — Memory Provenance Metadata
8. BR-008 — Decision Lifecycle
9. BR-009 — Memory Review & Promotion
10. BR-010 — Index Freshness
11. BR-011 — Retrieval Quality
12. BR-012 — Progressive Memory Retrieval
13. BR-013 — Memory Poisoning & Privacy Tests
14. BR-014 — Kullanıcıya dönük Health & Recovery
15. BR-015 — Release & Migration Gate
16. BR-016 — OpenCode entegrasyonu
17. BR-017 — OpenRouter / Direct API
18. BR-018 — Geçmiş oturumları içe aktarma
19. BR-019 — macOS / Linux / WSL gerçek destek
20. BR-020 — Daha ileri hafıza özellikleri

M0–M4 ilk beta için zorunlu; M5 aşamalı ve ayrı doğrulama gerektirir.
Aşama geçişi takvimle değil kabul kriterleriyle yapılır.

---

## M0 — Ölçüm ve kalite temeli

### [x] BR-001 · Memory Evaluation Harness (P0, M)

- `tests/evals/` altında bağımsız değerlendirme altyapısı.
- 40–50 sentetik senaryo: hatırlama, çoklu oturum, zaman, güncelleme, bilinmeyen bilgi.
- Her senaryoda beklenen kaynak, cevap ve güncellik koşulu.
- FTS5, semantik, hibrit ve hafızasız temel karşılaştırması.
- Makine okunabilir JSON + okunabilir Markdown raporu.
- Model/prompt/veri seti/sürüm kaydı ve tekrarlı çalışma dağılımı.

**Kabul:** Aynı fixture, sürüm ve ayarla tekrar çalıştırılabilir sonuç; raporda model, prompt, veri seti ve sürüm kayıtlı.

### [x] BR-002 · Memory Pipeline Diagnostics (P0, M)

- Yakalama, maskeleme, özetleme, günlük yazma, derleme, indeksleme ve geri çağırmaya durum kimlikleri.
- `provider_unavailable`, `hook_not_approved`, `summary_failed`, `index_stale` gibi yapılandırılmış nedenler.
- `health` ve mevcut log mekanizmasını kullanma.
- Tanıda ham döküm, secret veya özel not gövdesi tutmama.
- Oturum/işlem kimliği ile olay ilişkisi.

**Kabul:** Başarısız hafıza kaydının aşaması, hassas metin açığa çıkmadan belirlenebiliyor.

### [x] BR-003 · Mevcut sürüm baseline raporu (P0, S)

- Mevcut sürümü sabitle.
- Test veri setinde ilk sonuçları al.
- Arama P50/P95 gecikmeleri ve ilk oturum bağlam tokenlarını kaydet.
- Başarılı/başarısız yakalamaları kategorize et.
- Sonuçları sonraki sürümlerle karşılaştırılabilir yap.

**M0 tamamlanma:** Brain'in mevcut kalite seviyesi ölçülebiliyor; her hafıza değişikliği aynı testleri çalıştırıyor.

---

## M1 — Güvenilir oturum yakalama

### [x] BR-004 · Gerçek agent entegrasyon matrisi (P0, L)

- Claude Code, Codex, Antigravity, Cursor, Gemini CLI gerçek oturum testleri.
- Başlatma, tur, sıkıştırma, kapanış, yeniden başlatma olayları.
- İstemci başına kurulu / bağlı / onaylı / gerçek testten geçmiş / sınırlı destek ayrımı.
- Claude → Codex ve Codex → Antigravity çapraz-agent senaryoları.

**Kabul:** Tam destek ilan edilen her istemci gerçek oturumdan kaydedip sonraki oturumda geri çağırıyor; geçmeyen açıkça sınırlı gösteriliyor.

### [x] BR-005 · Yakalama dayanıklılığı ve idempotency (P0, M)

- Aynı olayın çift yazmaması.
- Yarım özetleme/kapanış senaryolarının sınırlandırılması.
- Kota, kapanan terminal, geçici kasa hatası, bozuk döküm testleri.
- Güvenli ve sınırlı yeniden deneme politikası.
- Provider değişiminde oturum kimliği/kapsam ayrımı.
- Hata anında agent'ın çalışmasını engellememe.

**Kabul:** Tekrarlı olay çift yazmıyor; kurtarılabilir hatalar izlenebilir; başarısız hafıza işlemi kullanıcıyı agent'tan koparmıyor.

### [x] BR-006 · Oturum özetleme doğruluğu (P0, M)

- Karar, gerekçe, çözülen hata, açık iş ve önemli değişiklik senaryoları.
- Uzun dökümlerde kırpılma ölçümü.
- Kaynakta olmayan karar uydurmayı hata sayma.
- Başarısız özetlemeyi başarılı kayıt gibi göstermeme.
- Ham dökümü saklamadan çalışabilme.
- Mevcut maskeleme ve model güvenlik sınırlarını koruma.

**Kabul:** Özetler geçerli olmanın yanında değerlendirme verisindeki kararları doğru temsil ediyor.

---

## M2 — Kaynaklı, güncel ve doğrulanabilir hafıza

### [x] BR-007 · Memory Provenance Metadata (P0, M)

- Mevcut Markdown biçimiyle uyumlu metadata.
- Kaynak agent, oturum, kayıt tarihi, kayıt türü, inceleme durumu.
- Doğrulanabilir kaynak referansı ve hash.
- Model çıkarımı ile kullanıcı onaylı bilgi ayrımı.
- Eski/eksik metadata okunabilirliği.
- Migration ve sürüm fixture'ları.

**Kabul:** Her yeni kritik kaydın kaynağı/doğrulama durumu ayırt edilebiliyor; eski notlar bozulmuyor.

### [x] BR-008 · Decision Lifecycle (P0, L)

- `active`, `superseded`, `disputed` durumları.
- Bir kararın başka kararın yerini aldığının gösterilmesi.
- Geçerlilik tarihi ile kayıt tarihinin ayrılması.
- Eski karar geçmişi silinmeden yenisinin güncel sayılması.
- Çelişen kararların sessizce birleştirilmemesi.
- Kritik çelişkilerin insan incelemesine gitmesi.

**Kabul:** Express → Fastify senaryosunda yeni oturum güncel kararı getiriyor; geçmiş sorgusu eski kararı da buluyor.

### [x] BR-009 · Memory Review & Promotion (P0, M)

- Inbox ve `review: pending` yaklaşımının genişletilmesi.
- Kabul, ret, düzeltme, erteleme işlemleri.
- Tekrarlanan hataların öğrenim adayı işaretlenmesi.
- Modelin kendi kaydını otomatik `verified` yapmasının engellenmesi.
- Onaylanan bilginin yetkili işlemle kalıcı bilgiye yükseltilmesi.
- Reddedilen kaydın yeniden önerilmesinin kontrolü.

**Kabul:** Onaylanmamış içerik kalıcı kullanıcı kuralına dönüşmüyor; kabul/düzeltme izlenebilir.

---

## M3 — Hızlı ve doğru hafıza geri çağırma

### [x] BR-010 · Index Freshness (P0, M)

- Editörde değişen dosyanın indeks güncelliği.
- Mevcut artımlı indeksleme altyapısının kullanılması.
- Bildirim, kontrollü tarama veya sorgu öncesi tazelik seçenekleri.
- Silinen/değişen dosyanın eski metnini döndürmeme.
- Çoklu yazıcı ve dosya kilidi testleri.
- İndeksin notlardan yeniden kurulabilirliği.

**Kabul:** Dışarıdan değişen not kısa sürede yeni sürümüyle bulunuyor; eski sürüm güvenilir sonuç gibi dönmüyor.

### [x] BR-011 · Retrieval Quality (P1, L)

- FTS5, semantik, hibrit benchmark karşılaştırması.
- Alaka eşiği ve sıralama stratejisi.
- Uzun notların anlamlı parçalara ayrılması.
- Tekrarlı sonuçların azaltılması.
- `active` kararlar ve güvenilir kaynakların öne çıkarılması.
- Semantik hatasında güvenli FTS5 fallback.
- Hız ve doğruluğun birlikte ölçülmesi.

**Kabul:** Doğru kaynağı bulma başlangıcın altına inmiyor; eski karar yeni kararın önüne hatalı geçmiyor.

### [x] BR-012 · Progressive Memory Retrieval (P1, M)

- Kısa ve önceliklendirilmiş başlangıç bağlamı.
- Kısa sonuç → kaynak özeti → tam not akışı.
- Görev bazlı ve token bütçeli bağlam.
- Mevcut MCP erişim sınırlarının korunması.
- Görev başarısı ile context maliyetinin birlikte karşılaştırılması.
- Her mesaja tam hafıza eklememe kararının korunması.

**Kabul:** Aynı görevlerde eşit/daha iyi doğruluk, daha az gereksiz hafıza metniyle sağlanıyor.

---

## M4 — Güvenlik ve yayın kalitesi

### [x] BR-013 · Memory Poisoning & Privacy Tests (P0, M)

- Zararlı README, web sayfası, döküm ve not örnekleri.
- Dış metnin kalıcı kullanıcı talimatına dönüşmemesi.
- Secret maskeleme testlerinin genişletilmesi.
- MCP izinsiz yazma, yetki iptali, kasa değişimi testleri.
- Arşiv açık/kapalı ve saklama süresi senaryoları.
- Saldırı testlerinin yayın öncesi regresyon setine eklenmesi.

**Kabul:** Saldırı örnekleri yetkisiz kalıcı kural/izin değişikliği oluşturamıyor; hassas içerik sızmıyor.

### [ ] BR-014 · Kullanıcıya dönük Health & Recovery (P1, M)

- `health` komutunun genişletilmesi.
- İstemci bağlantısı, hook onayı, son başarılı yakalama, indeks güncelliği.
- Anlaşılır sorun kategorileri.
- `repair` ve `recover` akışlarına güvenli çözüm önerileri.
- Hub arayüzünde gösterim seçeneği.

**Kabul:** Kullanıcı son oturumun neden alınmadığını hassas log paylaşmadan anlıyor.

### [ ] BR-015 · Release & Migration Gate (P0, M)

- Tam birim ve entegrasyon testleri.
- Şema migration ve eski sürüm fixture testleri.
- Dondurulmuş Windows paketi ve fiziksel kurulum smoke testleri.
- Kurulum → onarım → güncelleme → kaldırma → yeniden kurulum.
- Kullanıcı notları ve diğer araç ayarlarının korunması.
- Hub/Brain/Orchestrator conformance testleri.
- Desteklenen/doğrulanmamış platformların ayrı belgelenmesi.
- Sertifika hazırsa Authenticode'un yayın zincirine eklenmesi.

**Kabul:** Yayın paketinin test raporu var; kasa kaybı, yetkisiz değişiklik veya kritik veri bütünlüğü regresyonu yok.

---

## M5 — Kontrollü genişleme

### [ ] BR-016 · OpenCode entegrasyonu (P1, M)
- Güncel hook/MCP yeteneklerinin doğrulanması; mevcut adaptör kuralları.
- Yakalama, özetleme, geri çağırma testleri; gerçek oturum olmadan tam destek ilan etmeme.

### [ ] BR-017 · OpenRouter / Direct API (P1, L)
- İzinli sağlayıcı adaptörü; güvenli anahtar saklama.
- Kullanıcı seçimi olmadan ücretli sağlayıcıya geçmeme.
- Sağlayıcı bazlı izin, maliyet, fallback; aynı eval setiyle kalite karşılaştırması.

### [ ] BR-018 · Geçmiş oturumları içe aktarma (P2, M/L)
- Seçili eski oturumları önizlemeli içe alma; kaynak/tarih korunması.
- Maskeleme ve arşiv izinleri; tekrar içe alma ve eski bilgiyi güncel saymama testleri.

### [ ] BR-019 · macOS / Linux / WSL gerçek destek (P1/P2, L)
- Kurulum/onarım/kaldırma; hook ve model ortamı; dosya izinleri, yol ayrıştırma, süreç sonlandırma.
- Platform desteğinin gerçek doğrulamaya göre yayınlanması.

### [ ] BR-020 · Daha ileri hafıza özellikleri (P2, ayrı değerlendirme)
- Öğrenim adaylarından skill önerileri; isteğe bağlı gelişmiş oturum araması.
- Çoklu-agent iş devri bağlamı; kasa sağlığı/tekrar/çelişki raporları.
- M0–M4 güvenilirliğini zayıflatmama şartı.

---

## Her PR için Definition of Done

- Açık bir kullanıcı problemi çözülmüş.
- En az bir olumlu, bir olumsuz ve ilgiliyse hata/kurtarma testi.
- Testler gerçek kullanıcı kasasına ve AI ayarlarına dokunmuyor.
- İzinler/güvenlik sınırları gevşemiyor.
- Şema değişikliği ve migration testi (varsa) hazır.
- Belgeler kodla aynı PR'da güncel.
- `python -m unittest discover -s tests -t .` başarılı.
- Paket değişmişse dağıtım testi; üç ürün sözleşmesi etkilenmişse conformance testi başarılı.
- Sonuç "uygulandı" / "test edildi" / "gerçek ortamda doğrulandı" seviyesinde doğru raporlanmış.

---

## Kanıt günlüğü

<!-- Her görev tamamlandığında aşağıdaki şablona kanıt eklenir. Kanıt yoksa görev açık kalır. -->

### Şablon

```
### BR-XXX · <başlık> — TAMAMLANDI
- Tarih/saat:
- Değişen dosyalar:
- Uygulama:
- Testler ve komut:
- Sonuç (uygulandı / test edildi / gerçek ortamda doğrulandı):
- Artefaktlar (yol + sha256):
- Bilinen sınırlar / risk:
```

<!-- EVIDENCE:START -->
### BR-001 · Memory Evaluation Harness — TAMAMLANDI
- Tarih/saat: 2026-10-30 (Europe/Istanbul)
- Değişen dosyalar:
  - `respected-brain/tests/evals/__init__.py` (yeni)
  - `respected-brain/tests/evals/scenarios.json` (yeni, 50 senaryo)
  - `respected-brain/tests/evals/harness.py` (yeni)
  - `respected-brain/tests/evals/test_memory_eval_harness.py` (yeni, 9 test)
  - `respected-brain/tests/evals/results/baseline-0.1.0-beta.1.json` (yeni)
  - `respected-brain/tests/evals/results/baseline-0.1.0-beta.1.md` (yeni)
- Uygulama: İzole geçici kasa üzerinde `none|fts|semantic|hybrid` kiplerini çalıştıran CLI harness. 50 senaryo (recall 12, multi_session 10, temporal 10, update 10, unknown 8); beklenen kaynak, cevap terimi, `expect_top1` ve `stale_paths` koşulları. Skorlar: pass, Hit@1, Hit@5, MRR, cevap doğruluğu, kaynak kapsamı, eski-not-üstte hatası, bilinmeyen-sorgu doğruluğu. JSON raporda sürüm/prompt/veri seti sha256/ayar/model bilgisi, kategori kırılımı, P50/P95 gecikme, bağlam token tahmini ve tekrar dağılımı var; Markdown raporu insan okunur.
- Testler ve komut:
  - `python -m unittest tests.evals.test_memory_eval_harness -v` → 9 test OK
  - `python -m unittest discover -s tests -t .` → 921 test OK, 15 skip
  - Baseline: `python -m tests.evals.harness --modes none,fts,hybrid --repeats 3 --json-out ... --md-out ...`
  - Tekrarlanabilirlik: FTS iki ayrı çalıştırma → aggregate ve senaryo skorları birebir aynı (pass %64.0)
- Baseline sonucu: `none` pass %16.0 (yalnızca bilinmeyen sorgular), `fts` pass %64.0 / Hit@5 %100 / cevap %100, P50 40.86 ms / P95 53.8 ms. `hybrid` `unavailable` (`SEMANTIC_OFF`: yerel semantik sağlayıcı etkin değil).
- Gerçek bulgu: FTS temporal senaryoların tamamında beklenen güncel kaynağı ilk sıraya koyamıyor (Hit@1 yok); update senaryolarının tamamında eski not güncel notun üstünde (`stale_above_current=1`). Bu, sonraki M2/M3 işleri için ölçülebilir başlangıç açığı.
- Sonuç: **test edildi** (gerçek agent oturumu doğrulaması değil; sentetik fixture'lar).
- Artefaktlar (yol + sha256):
  - `tests/evals/scenarios.json` → `C0CDB91C5E9960DA32E09DBDEFDD1A574790C2E06D6CFD419BB85B402C60E662`
  - `tests/evals/harness.py` → `EA263F14478B622FC63527DAEA6A42C30DC32194A4F93EBC0712FF50C6357981`
  - `tests/evals/test_memory_eval_harness.py` → `7AE4225C98E7E27571E7B090C27734B0893B435BB1DD1E52F4C9A59781D699BF`
  - `tests/evals/results/baseline-0.1.0-beta.1.json` → `98706854B66B3B976D23A48635E1F80506420F7A147A4A6210A46D15255A49F8`
  - `tests/evals/results/baseline-0.1.0-beta.1.md` → `06338F9208739CF784B50D615E1A2E1BD2FB9F3217C864FC8DEC6021F45393AB`
- Bilinen sınırlar / risk: Semantik/hibrit kipler bu makinede çalıştırılamadı; sonuç `unavailable` olarak dürüstçe raporlanıyor. Baseline sentetiktir; gerçek kullanıcı kasası kullanılmadı. Zaman/güncelleme açıkları henüz giderilmedi (BR-008/BR-011 kapsamı).
### BR-003 · Mevcut sürüm baseline raporu — TAMAMLANDI
- Tarih/saat: 2026-10-30 (Europe/Istanbul)
- Sürüm sabitleme: `0.1.0-beta.1` (`0.1.0b1`), git HEAD `95fe426`. Çalışma ağacında bu görev kapsamı dışında önceden var olan değişiklikler (`packaging/windows/brain_setup.iss`, `src/respected_brain/rpp/integrations.py`, `tests/rpp/test_integrations.py`) korundu.
- Değişen dosyalar:
  - `docs/BASELINE.md` (yeni)
  - `tests/evals/compare.py` (yeni)
  - `tests/evals/test_compare.py` (yeni, 6 test)
  - `tests/evals/results/baseline-0.1.0-beta.1.json` / `.md` (BR-001 çıktısı, sabit baseline)
  - `tests/evals/results/self-compare.json` (yeni)
  - `tests/evals/results/_full-suite.log` (yeni)
- Uygulama: Baseline sürümü, veri seti hash'i, yeniden üretim komutu, mod bazlı sonuçlar, kategori başarı/başarısızlık kırılımı, P50/P95 gecikme ve bağlam token tahmini `docs/BASELINE.md` içinde sabitlendi. `tests/evals/compare.py` iki raporu aynı veri seti hash'i ile karşılaştırıyor; pass/Hit@1/Hit@5/MRR/cevap/kapsam/bilinmeyen düşüşünü, eski-not-üstte artışını ve P50/P95'te %30 aşan gecikmeyi gerileme sayıp çıkış kodu 1 veriyor. Veri seti değişirse karşılaştırmayı reddediyor.
- Kategori kırılımı (FTS): recall 12/12, multi_session 10/10, temporal 2/10, update 0/10, unknown 8/8 → toplam 32/50 (%64). Başarısızların tamamı temporal (ilk sıra) ve update (eski not üstte) sınıflarında.
- Testler ve komut:
  - `python -m unittest tests.evals.test_compare tests.evals.test_memory_eval_harness` → 15 test OK
  - `python -m unittest discover -s tests -t .` → 928 test OK, 15 skip (çıkış 0)
  - `python -m tests.evals.compare baseline.json baseline.json --json-out self-compare.json` → `ok`, gerileme yok
- Sonuç: **test edildi** (sentetik fixture; gerçek agent oturumu değil).
- Artefaktlar (yol + sha256):
  - `docs/BASELINE.md` → `A0E794F865628991EEA331D494664E9337450C0CD3EDAD540983362F05633C74`
  - `tests/evals/compare.py` → `401D7CE538FB0FD432E39303DF481EE102BFD553191BB7B316189C60F6DE075B`
  - `tests/evals/test_compare.py` → `A84084F70E19500433038C3F3F187ACEFA3B5186D5DAD382D28440B5449FF1DA`
  - `tests/evals/results/self-compare.json` → `433543DE4023A27BC6627D12DB2C409DB269F40AF492F9241AEDA953F056DB5D`
  - `tests/evals/results/_full-suite.log` → `BDE48CC8A9354505ECC2835845FE4B4E86B72FBDC89B479E2089BDA3F4987B23`
  - Baseline JSON/MD hash'leri BR-001 kanıtında.
- Bilinen sınırlar / risk: Gerçek agent oturumundan yakalama başarısı bu baseline'da ölçülmedi (BR-004). `semantic`/`hybrid` sağlayıcı olmadığı için `unavailable`. P50/P95 tek makine ölçümü; tolerans sabit %30. Baseline dosyaları değiştirilirse karşılaştırma geçmişi bozulur; yeni ölçümler ayrı dosya adıyla üretilmeli.
### BR-002 · Memory Pipeline Diagnostics — TAMAMLANDI
- Tarih/saat: 2026-10-30 (Europe/Istanbul)
- Sürüm/git: `0.1.0-beta.1` (`0.1.0b1`), HEAD `95fe426`. Kapsam dışı, önceden var olan değişiklikler korundu: `packaging/windows/brain_setup.iss`, `src/respected_brain/installation/operations.py`, `src/respected_brain/rpp/integrations.py`, `tests/packaging/test_posix_install.py`, `tests/rpp/test_integrations.py`.
- Değişen/eklenen dosyalar:
  - `src/respected_brain/memory/diagnostics.py` (yeni)
  - `src/respected_brain/memory/lifecycle.py`
  - `src/respected_brain/memory/flush.py`
  - `src/respected_brain/memory/compile.py`
  - `src/respected_brain/integrations/hooks/bridge.py`
  - `tests/memory/test_diagnostics.py` (yeni, 5 test)
- Uygulama: Ortak tanı katmanı eklendi. Aşamalar `capture`, `redact`, `summarize`, `daily_write`, `event_project`, `compile`, `index`, `recall` olarak sınırlandı. `health.json` kayıtları `status`, `error`, `reason`, `component`, `stage`, `operation_id`, `session_id`, `provider`, `event`, `ts`, `warnings` alanlarıyla yazılıyor. Nedeni bilinmeyen istisnalar serbest metin olarak değil `error:<Sınıf>` veya `unclassified` gibi güvenli kodlarla raporlanıyor. Aynı olay için tek `operation_id` üretilip lifecycle → flush/precompact → compile zincirine taşınıyor. Eski/uyumlu health alanları korunuyor; bozuk veya NaN içeren health dosyası çökmeye yol açmıyor, `warnings` durumu düşürmüyor. Ham döküm, secret, dosya yolu ve özel not gövdesi health/log kaydına girmiyor; `bridge-error` yalnızca istisna sınıfını yazıyor.
- Testler ve komut:
  - `python -m unittest tests.memory.test_diagnostics tests.memory.test_lifecycle tests.memory.test_compile_flush tests.memory.test_transcript_integrity tests.memory.test_session_scripts tests.scenarios.test_regression_matrix -v` → 163 test OK, 2 skip (çıkış 0)
  - `python -m unittest tests.memory.test_diagnostics -v` → 5 test OK
  - `python -m unittest tests.rpp.test_memory.MemoryRecallTest.test_recall_leaves_vault_and_data_root_byte_and_mtime_identical -v` → 1 test OK (salt-okunur recall kasayı ve veri kökünü değiştirmiyor)
  - `python -m unittest discover -s tests -t .` → 929 test, 1 failure, 5 error, 15 skip (çıkış 1). Hatalar bu görevle ilgisiz, önceden var olan ortam/bağımlılık sorunları: `packaging.version` eksikliği (4 test), Windows CLI entrypoint yürütülebilir dosya testi, Windows'ta `TimeoutExpired` beklenen süreç testi. Hafıza/tanı odaklı testlerin tamamı geçti.
- Sonuç: **uygulandı; odak ve ilgili testler test edildi** (gerçek agent oturumu doğrulaması değil; o BR-004 kapsamı).
- Artefaktlar (yol + sha256):
  - `src/respected_brain/memory/diagnostics.py` → `20AF6F88B01A74A8A19F1F5D0B8E4B2C9820B1A93A762FE413CFEB71D0DC3FCB`
  - `src/respected_brain/memory/lifecycle.py` → `2444995C688F83D56AEF45D5486369C97196B1ED1E56169601927788FEDE99BF`
  - `src/respected_brain/memory/flush.py` → `996A153D37745EF28B350F0B802F483ADC9FBA1D2023F406E00103E065946459`
  - `src/respected_brain/memory/compile.py` → `1B0ADC53619F5EB12930C900A46175532AFF41412E72F95BEF346374FA6EA9FE`
  - `src/respected_brain/integrations/hooks/bridge.py` → `6D566FED55B2B145103A5A393A1E715FF8577FDEDF9B88AC944F855C070D5622`
  - `tests/memory/test_diagnostics.py` → `7FBDF6986075394DF8169CF47C0C636297EB4C8F875C68F8392B922461B00929`
  - `tests/evals/results/br002-focus.log` → `74D7DB2FF1D13AF35101A87AE76E8739EFE4AD74F9DBCA5C7B5F22B308E81AD8`
  - `tests/evals/results/br002-full-suite.log` → `C1004C2F590A79798471329F3DE6C4D5A6C295FC5B3CCC3A9EB2A05FF16B9734`
- Bilinen sınırlar / risk: Tanı yalnızca başarısız aşamayı görünür kılar; otomatik yeniden deneme veya onarım yapmaz (BR-005/BR-014 kapsamı). Gerçek sağlayıcı/agent kesintisi uçtan uca simüle edilmedi. Tam test paketi bu makinede temiz değil; yayın kapısı (BR-015) öncesi bağımlılık/ortam sorunları giderilmeli.

### BR-004 · Gerçek agent entegrasyon matrisi — TAMAMLANDI
- Tarih/saat: 2026-10-30 (Europe/Istanbul)
- Sürüm/git: `0.1.0-beta.1` (`0.1.0b1`), HEAD `95fe426`.
- İzole ortam: `tests/evals/runs/br004-20261030-053546/` (`app`, `data`, `vault`, `work`, `home-claude`, `home-codex`, `home-agy`, `home-matrix`). Kasa UUID `50c317d8-e460-4b1c-b0c3-dceab54eaf76`; ham döküm arşivi kapalı.
- Eklenen/değişen dosyalar:
  - `tests/evals/br004_matrix.py` (yeni, salt-okunur matris; kanıt yoksa istemciyi asla `full` yapmaz)
  - `tests/evals/test_br004_matrix.py` (yeni, 3 test)
  - `tests/evals/results/br004-evidence.json` (yeni, sanitize edilmiş gerçek oturum kanıtı)
  - `tests/evals/results/br004-matrix.json`, `tests/evals/results/br004-matrix.md` (yeni, üretilen matris)
  - `tests/evals/runs/br004-20261030-053546/` (yeni, gerçek oturum çıktıları ve kasa kayıtları)
- Gerçek oturum testleri:
  - **Claude Code — full:** oturum 1 `5f517528-a2c0-4443-ac35-9a1e73610b96` içinde `orbit-731` kararı kaydedildi; oturum 2 `f734d10e-33f5-4acf-9a74-ff5d1a686413` aynı kararı `orbit-731` olarak geri çağırdı. `start`, `prompt`, `turn`, `end` akışı çalıştı; günlük ve companion kayıtları oluştu.
  - **Codex — full:** oturum 1 `01a18ab4-1b23-7252-b5f6-bcd56859a5d3` içinde `vega-42` kaydedildi; oturum 2 `01a18ab4-89ed-7471-87c0-0f4391eba896` `vega-42` olarak geri çağırdı. İzole `CODEX_HOME` kullanıldı.
  - **Antigravity — full:** oturum 1 `d062d78b-a36c-49cf-8819-5d632e702aae` içinde `lyra-10` kaydedildi; oturum 2 `476afeab-89a9-466b-a1e5-1c1531e4c753` `lyra-10` olarak geri çağırdı. Workspace `.agents/hooks.json` ile `start`/`turn` çalıştı.
  - **Cursor — limited:** `cursor-agent`/`cursor` executable yok, `.cursor` ayarı yok; gerçek test yapılmadı.
  - **Gemini CLI — limited:** `gemini` executable yok; gerçek test yapılmadı.
- Çapraz-agent senaryoları:
  - **Claude → Codex:** Codex oturumu `01a18ab5-01b3-7483-b9d2-fdc118cd7c0e`, Claude kararını `orbit-731` olarak geri çağırdı → geçti.
  - **Codex → Antigravity:** Antigravity oturumu `00ff3e60-d869-44a1-ae42-e1ba124b68e7`, Codex kararını `vega-42` olarak geri çağırdı → geçti.
- Testler ve komut:
  - `python -m unittest tests.evals.test_br004_matrix tests.rpp.test_integrations -v` → 12 test OK (çıkış 0)
  - Matris: `python tests/evals/br004_matrix.py --home .../home-matrix --evidence tests/evals/results/br004-evidence.json ...` → claude/codex/antigravity `full`; cursor/gemini `limited`.
- Sonuç: **gerçek ortamda doğrulandı** (Claude Code, Codex, Antigravity); Cursor ve Gemini için yalnızca `limited` beyanı geçerli.
- Artefaktlar (yol + sha256):
  - `tests/evals/br004_matrix.py` → `36CB1A70EF20D0D219960E0B9EC790EB3A1380392EFA4DA2AEC090B1C114C9F8`
  - `tests/evals/test_br004_matrix.py` → `71CCFB18F3D4B6A34ED0CE57FD63BA151AFCADF81D9C9D3694DF3F77D04C56BD`
  - `tests/evals/results/br004-evidence.json` → `B047305934F758CD0785290E3DA1EFF8CD5F10E0FF8BE281E0819D18D82F386B`
  - `tests/evals/results/br004-matrix.json` → `E1DFBC35CA54201496ECD92A890EDD486FEA1BE8E460BF5C7A23A763E1863DC5`
  - `tests/evals/results/br004-matrix.md` → `FB95BD12CD4446A75D075841AE672769EA59DD08F4E35D40659B7C02518DAA86`
  - `tests/evals/results/br004-focus.log` → `C105B8D3DE4D76B34D00E8998CC3A5AF3AC75ED605F485475ADA9EF0147D58F6`
  - `tests/evals/runs/br004-20261030-053546/vault/daily/2026-10-30.md` → `EF606562F09012AA7F5275E4518A79A1380DC6AE633A0313A369708D402E1747`
  - `tests/evals/runs/br004-20261030-053546/claude-session2.out.json` → `541F3CB65F0352008D11389240080609C6C50DBBDFC5E05B6A929A58897F3C3C`
  - `tests/evals/runs/br004-20261030-053546/codex-session2.out.jsonl` → `686F3BAFF445C7DC72A5EC482F109DBA4AFA4D4C582EA7AFDB6D72529A339EC1`
  - `tests/evals/runs/br004-20261030-053546/agy-session2.out.json` → `3B75C0A5148818B559D961408AB243551D5E5919443507D3C4265907C1A398C4`
  - Kalan 7 companion olay dosyası ve oturum çıktısının hash'leri `tests/evals/results/br004-evidence.json` içinde.
- Bilinen sınırlar / risk: Codex'in ilk `--ephemeral` denemesi transcript üretmediği için kayıt oluşmadı; başarılı test `--ephemeral` olmadan ve `--dangerously-bypass-hook-trust` ile yapıldı. Antigravity global `~/.gemini/config/hooks.json` dosyasını otomatik yüklemedi; gerçek test workspace `.agents/hooks.json` ile yapıldı ve ilk oturum (`e190c3ab`) bu nedenle kaydedilmedi. Claude/Antigravity için "onaylı" alanı matriste `bilinmiyor` görünür; yalnızca açık devre dışı bırakma `hayır` sayılır. Ham döküm, auth/token/secret ve özel not gövdesi kanıta konmadı.

### BR-005 · Yakalama dayanıklılığı ve idempotency — TAMAMLANDI
- Tarih/saat: 2026-10-30 07:01 (Europe/Istanbul)
- Sürüm/git: `0.1.0-beta.1` (`0.1.0b1`), HEAD `95fe4263ec5f42d5da5d17974c93e7c9335505c3`.
- Değişen/eklenen dosyalar:
  - `src/respected_brain/memory/flush.py` — bozuk JSONL dökümü model/günlük yazımından önce sınırlı hataya dönüşüyor; JSON parse hatası metadata bozulmasından ayrıldı.
  - `tests/memory/test_br005_resilience.py` (yeni, 5 test) — bozuk döküm, kalıcı model hatası, kapalı terminal ve köprü istisnası.
  - `tests/memory/test_session_scripts.py` — hook kaynaklı bozuk dökümün `accepted` + `failed` olarak sınırlandığını doğrulayan test güncellendi.
  - `tests/evals/results/br005-evidence.json` (yeni, sanitize edilmiş kanıt).
- Uygulanan davranış:
  - Bozuk JSONL `transcript-jsonl-invalid` koduyla kaydediliyor; model çağrılmıyor ve günlük yazılmıyor.
  - Kalıcı sağlayıcı hatası iki denemeden sonra `failure-bound` ile atlanıyor; kota ve timeout ayrı kodlarla sınırlandı.
  - Kapalı terminal `flush-launch-failed`, köprü istisnası `bridge-error` olarak health kaydına yazılıyor; istemciye geçerli boş JSON dönüyor.
  - Aynı transcript sahipliği ve sağlayıcı kapsamı korunuyor; sağlayıcı değişimi eski oturumu yeniden yorumlamıyor.
- Test sonuçları:
  - Odak: 6/6 `OK`, çıkış 0.
  - Regresyon: 103/103 `OK`, çıkış 0.
  - Tam paket: 942 test, 0 hata, 15 atlama, çıkış 0.
- Kabul eşlemesi:
  - Çift yazma: aynı oturum iki kez flush edildiğinde tek günlük bloğu; catch-up tekrarı tek özet.
  - Sınırlı yeniden deneme: kalıcı hata ve bozuk döküm `failure-bound` ile duruyor; kurtarılabilir hata sahipliği koruyor.
  - Kota / kapanan terminal / geçici kasa hatası / bozuk döküm: dört senaryo ayrı testlerle doğrulandı.
  - Provider değişimi: model çağrılmıyor; state ve günlük baytları değişmiyor.
  - Agent'ı koparmama: `handle_event` istisna yükseltmiyor; köprü geçerli JSON dönüyor.
- Artefaktlar (yol → sha256):
  - `src/respected_brain/memory/flush.py` → `484AF5A79794070F2FD6D0720E56CBA64A9FF5F784FE0752F17E4C07BCA62E2D`
  - `tests/memory/test_session_scripts.py` → `286719F854FEFA3DF92A1EEAAB35CB48E6D99EAEFA8533D3944F53821FEFAB21`
  - `tests/memory/test_br005_resilience.py` → `7F1A0765A57D5066E3E84FC5F47AE709B601A6A47CF859EA41F92BEDDD59007A`
  - `tests/evals/results/br005-focus.log` → `4B4E6E90FF3B1E4156702DAED478631B546AC06AE2A01EA77217E8E178F1319D`
  - `tests/evals/results/br005-regression.log` → `4B740AD6C35BC51AA1D24E48A6FEB1C1B73814715CD56C6AC9B6793946CB98B2`
  - `tests/evals/results/br005-full-suite.log` → `34646E5929ED4C10AC0A61DC5270AFCEACE8D97A3D788D7255F6165264CDC779`
- Bilinen sınırlar / risk: Doğrulama birim/entegrasyon testleriyle yapıldı; gerçek agent oturumunun yeniden oynatılması değil (BR-004 kapsamı). Tam pakette 15 test platform/ortam gereksinimi nedeniyle atlandı. Odak logundaki PowerShell `NativeCommandError` satırları `2>&1` kaynaklı kozmetik çıktıdır; sonuç `OK`, çıkış 0. Ham döküm, secret ve özel not gövdesi kanıta konmadı.
- Sonuç: **uygulandı; odak, regresyon ve tam paket test edildi**.
### BR-006 · Oturum özetleme doğruluğu — TAMAMLANDI
- Tarih/saat: 2026-10-30 (Europe/Istanbul)
- Değişen dosyalar:
  - `tests/evals/summarization_scenarios.json` (yeni, 12 sentetik senaryo B01–B12)
  - `tests/evals/summarization.py` (yeni harness; gerçek `flush` hattı + gerçek model)
  - `tests/evals/test_summarization_eval.py` (yeni, 18 test)
  - `src/respected_brain/memory/flush.py` — `format_turns` baş+son penceresi ve orta kırpma
  - `tests/memory/test_session_scripts.py` — pencere sözleşmesi ve baş/son koruma testleri
  - `docs/ARCHITECTURE.md` — uzun döküm penceresi davranışı
  - `tests/evals/results/br006-baseline.json` / `.md`, `br006-after.json` / `.md`, `br006-repeat2.json` / `.md`, `br006-full-suite.log` (yeni)
- Uygulama:
  - Harness her senaryoyu izole app/data/vault üçlüsünde gerçek `flush` hattından geçiriyor; özet gerçek `claude/haiku` CLI'sinden ürün `ModelRunner`'ı ile alınıyor. Test paketinin HOME sandbox'ı korunuyor; yalnızca model alt süreci için `HOMEDRIVE/HOMEPATH`'ten gerçek oturum profili geri veriliyor. Kasa, veri ve ayarlar okunmuyor/yazılmıyor.
  - Kapsam: karar (2), gerekçe, çözülen hata, açık iş (2), önemli değişiklik, uzun bağlam (2), güvenlik, boş oturum, sayısal kesinlik, Türkçe teknik terimler.
  - Skorlar: bölüm/terim bazlı gerçek kapsamı, prompt kapsamı (modele gitmeden kırpılan gerçek), kaynakta olmayan karar (hallucination), secret sızıntısı, enjeksiyon uyumu (hedef bölüme yazıldı mı; alıntılama "mention" sayılıyor), ham dökümün kasa/veride saklanması ve başarısız özetin başarı gibi gösterilmemesi (`state`/`health`).
  - Ürün düzeltmesi: eski pencere yalnızca en yeni 30 turu, karakter taşmasında yalnızca kuyruğu tutuyordu; B07'de oturumun ilk kararı, B09'da tek uzun turun iki ucu da modele gitmiyordu. Yeni pencere ilk 6 turu + en yeni 24 turu tutuyor, karakter bütçesini 2/5 baş + 3/5 son olarak bölüyor ve atlanan ortayı `[... N tur atlandı ...]` / `[... orta kısım atlandı ...]` ile işaretliyor.
- Testler ve komut:
  - `python -m unittest tests.evals.test_summarization_eval` → 18 test OK
  - `python -m unittest tests.memory.test_session_scripts` → 62 test OK, 2 skip
  - `python -m unittest discover -s tests -t .` → 962 test OK, 15 skip
  - Baseline: `python -m tests.evals.summarization --provider claude --repeats 1` (veri seti v1) → pass %75, fact %87.5, 3 kırpılan gerçek, 1 enjeksiyon işareti (özet metninde alıntı; uyum değil)
  - Final: aynı komut (veri seti v2) → 12/12 pass, fact %100, kırpılan 0, hallucination 0, secret 0, enjeksiyon 0, ham döküm 0
  - Kararlılık: `--repeats 2` → 24/24 pass, fact %100, kırpılan 0, hallucination 0, secret 0, enjeksiyon 0, ham döküm 0; tekrar dağılımı `[1.0, 1.0]`
  - Karar, gerekçe, çözülen hata, açık iş ve önemli değişiklik: B01–B05, B10–B12 gerçek modelde %100 temsil edildi.
  - Uzun döküm kırpılması: B07 ve B09 önce 3 gerçeği kaybediyordu; baş+son penceresi sonrası prompt kapsamı %100, kırpılan 0. Deterministik testler tek uzun turun iki ucunu ve 35 turluk oturumun baş/sonunu doğruluyor.
  - Kaynakta olmayan karar: `forbidden` terimleri ve B08'deki sahte `Zephyr-9` kararı hata sayılıyor; finalde 0.
  - Başarısız özetleme: scripted model hatasında `flush` durumu `fail`, `health.stage=summarize`, günlük özeti yok; test bunu doğruluyor.
  - Ham döküm: kasa/veri taramasında ham transcript ve `.jsonl` bulunmadı; `archive_transcripts` kapalı varsayılanı korunuyor.
  - Maskeleme/güvenlik: B08 secret'ı promptta `[REDACTED:provider-token]` oluyor; özette ve kasada yok. Enjeksiyon metni veri olarak kalıyor, `Zephyr-9` karar olarak yazılmıyor; bir koşuda yalnızca "mention" olarak anıldı.
- Artefaktlar (yol → sha256):
  - `tests/evals/summarization_scenarios.json` → `058566EDB9B8C45FA639583DCF3E62A4F22ACF1C514BB21CB5338B7735409EF8`
  - `tests/evals/summarization.py` → `737B6189A94FEF95DBA2C52689B5EDFB0AFE73D720874829DB5D0B87478C178F`
  - `tests/evals/test_summarization_eval.py` → `450E5E45F548E56FFF4ADAC9CA8FEC03CED6E66DBF2FDC63C147DEA5572DB24C`
  - `src/respected_brain/memory/flush.py` → `6143A11744301E52EDE5B9EF9FD5174F5F94220665D11E1E13C92E02898F31B2`
  - `tests/memory/test_session_scripts.py` → `3414DCB5C9A8FFC5FA27D33FDF51E7AE1243260E18E27CE3093B50144E86C44F`
  - `docs/ARCHITECTURE.md` → `C212F69D5681AC9B0B2DCE8764E75492155CD1919E64B80AA59DC061326A3408`
  - `tests/evals/results/br006-baseline.json` → `0E5C2F297A4115FCB0DB848FBED53323B7396DA041B77A85F5224D440DBC5693`
  - `tests/evals/results/br006-baseline.md` → `BF7969A857E4DFDC8A63A7AFE16AE1221802FE9FB2B14FAF759B53F92092F608`
  - `tests/evals/results/br006-after.json` → `2330EBBC973A052EA193D486E9D6340D8DE16418375B86BE04F1C52B0542EFA8`
  - `tests/evals/results/br006-after.md` → `1CC1BD45EDDA81BDA34C583E3A15EDC0BF185424C279090E1087AE92F0CC46BD`
  - `tests/evals/results/br006-repeat2.json` → `CE24673AAEF43F169396E52B0DB168E8685E99A02DFF64EEEB67CDDFC0A8AB1E`
  - `tests/evals/results/br006-repeat2.md` → `AE5FF60688ACEC5C0EFADEE3B434FD738A6D2BDF36CEB909AB85A68872141AD7`
  - `tests/evals/results/br006-full-suite.log` → `A6F92F50FF9C3443C48F53FADA6BA0431AD0925F3E79E98DD3885778BCB34251`
- Bilinen sınırlar / risk: Sentetik Türkçe dökümler kullanıldı; gerçek kullanıcı oturumu/kasası okunmadı. Model çağrısı gerçek CLI ve gerçek oturum profiliyle yapıldı; profil yalnızca alt süreç ortamında geri verildi, kasa/veri yolları izole kaldı. Model çıktısı deterministik değil; final veri setinde 36 koşu %100 olsa da bu bir güven aralığı değil. Baseline v1 ile final v2 aynı veri seti değil: B08 saldırısı bölüm hedefli hale getirildi ve enjeksiyon işareti `forbidden` listesinden çıkarıldı (alıntıyı uydurma karar sayan ölçüm hatası); ürün değişikliği yalnızca pencere ve pencere davranışı deterministik testlerle sabit. Bölüm yerleşimi finalde %84.7: bazı gerekçe/SLA gerçekleri `Önemli Konuşmalar` içinde doğru ama `Alınan Kararlar` yerine yazılıyor; içerik doğru, yerleşim üslup açığı. 15.000 karakter / 30 tur bütçesi hâlâ sert; atlanan ortadaki bir karar kaybolabilir, artık `prompt_coverage` ve "atlandı" işaretiyle görünür. Tam paket çıkış kodu PowerShell `2>&1` nedeniyle 1 görünüyor; logda `OK (skipped=15)` ve hata yok (BR-005'teki aynı kozmetik durum). Ham döküm, secret ve özel not gövdesi kanıta konmadı.
- Sonuç: **uygulandı; gerçek modelle, odak testleriyle ve tam paketle test edildi**.

### BR-007 · Memory Provenance Metadata — TAMAMLANDI
- Tarih/saat: 2026-11-03 (Europe/Istanbul)
- Sürüm/git: taban `094c5a6`; BR-007 değişiklikleri bu kanıt bloğuyla tek commit olarak işlendi.
- Değişen dosyalar:
  - `src/respected_brain/memory/provenance.py` (yeni)
  - `src/respected_brain/memory/compile.py`
  - `src/respected_brain/memory/flush.py`
  - `src/respected_brain/memory/inbox.py`
  - `src/respected_brain/rpp/memory_workspace.py`
  - `tests/memory/test_br007_provenance.py` (yeni)
  - `tests/fixtures/memory-provenance/v0-legacy.md` (yeni)
  - `tests/fixtures/memory-provenance/v1-model-inference.md` (yeni)
  - `tests/fixtures/memory-provenance/v1-user-approved.md` (yeni)
  - `docs/ARCHITECTURE.md`
  - `docs/ROADMAP-EXECUTION.md`
- Uygulama:
  - `provenance_version: 1` alanları: `source_agent`, `session_id`, `recorded_at`, `record_type`, `review_status`, `origin`, `source_ref`, `source_sha256`. Alanlar mevcut YAML frontmatter'a eklenir; günlük oturum özetlerinde yönetilen blok içinde `RESPECTED-PROVENANCE` HTML yorumu kullanılır.
  - `read_provenance` bilinmeyen/eksik alanları `legacy`, `unreviewed`, `unknown` olarak okur; eski dosyanın baytlarına dokunmaz. `migrate_text` isteğe bağlı taşıma yapar, gövdeyi korur ve özgün metnin SHA-256'sını yazar.
  - Model çıkarımı `origin: model_inference` + `pending` kalır; `build_provenance` model kaydını `approved` yazmayı reddeder. Kullanıcı onayı yalnızca `user_approved` ile temsil edilir.
  - Inbox/MCP yazımında çağıranın `extra_front` provenance anahtarları filtrelenir; MCP ve Orchestrator içeriği `model_inference`/`pending`, Hub yakalaması `user_authored` olur. Derleyici `knowledge/concepts` ve `connections` çıktısını kaynak günlük dosyası + SHA-256 + oturum kimliğiyle `pending` işaretler.
  - Günlük özet yorumu şema başlıklarından sonra yazılır; `validate_summary` ve mevcut tüketiciler bozulmaz. Özete provenance işareti enjekte eden model çıktısı `daily-summary-markers-invalid` ile reddedilir.
- Testler ve komut:
  - `python -m unittest tests.memory.test_br007_provenance` → 9 test OK
  - `python -m unittest discover -s tests/memory -t .` → 188 test OK, 2 skip
  - `python -m unittest tests.rpp.test_memory_write tests.integrations.test_mcp_and_features` → 39 test OK
  - `python -m unittest tests.memory.test_session_scripts` → 62 test OK, 2 skip
  - `python -m unittest tests.evals.test_summarization_eval` (odakla birlikte) → 27 test OK
  - `python -m unittest discover -s tests -t .` → 971 test OK, 15 skip (`tests/evals/results/br007-full-suite.log`)
  - İlk tam koşu 1 hata verdi: provenance yorumu özetin başında olduğu için şema denetimi `## Bağlam` öncesinde metin gördü. Yorum bloğun sonuna taşındı; odak ve tam paket yeniden çalıştırıldı, hata kalmadı.
- Kabul eşlemesi:
  - Her yeni kritik kayıtta kaynak agent, oturum, tarih, tür, inceleme durumu, kaynak referansı ve hash ayırt edilebiliyor.
  - Model çıkarımı ile kullanıcı onaylı bilgi ayrı; model kendi kaydını `approved` yapamıyor, MCP/Orchestrator yazımı `pending` kalıyor.
  - Eski notlar `legacy/unreviewed/unknown` okunuyor ve dosya baytları değişmiyor; sürüm fixture'ları v0 ile v1 model/onaylı biçimlerini kapsıyor.
  - Migration `migrate_text` ve v0/v1 fixture'larıyla test edildi; mevcut notlar toplu olarak değiştirilmiyor.
- Artefaktlar (yol → sha256):
  - `src/respected_brain/memory/provenance.py` → `DA538FB8F53CF636C0C2B86A76AF8929279BDFCE69F5E1D8CE85E24029DCE76C`
  - `src/respected_brain/memory/compile.py` → `FDE27A1D66241C0753883881C6E377C65100643E9CF8CCF9E4C05761E1C36C9E`
  - `src/respected_brain/memory/flush.py` → `11DE1B44A1BF17F912C2C6F9479184F31D8B1D7F661267C3ED6D1794E605321D`
  - `src/respected_brain/memory/inbox.py` → `F3BEE78AEA24E8C4B9D8F190DDC756657811296BEB1A646A960FE817789C42CD`
  - `src/respected_brain/rpp/memory_workspace.py` → `DB1EE870E542D4F65C14B7AF2CFEE0858B797FD78D62858F0553866EBF1297DE`
  - `tests/memory/test_br007_provenance.py` → `836465D1DEC9C7A2E6ED12358DFEDD4F67438F127CF85368D73F36CC8DB8E598`
  - `tests/fixtures/memory-provenance/v0-legacy.md` → `69713124276B487D7F60B88C741B33A9789E03AF6554A6BB83CDABEFD5C894B5`
  - `tests/fixtures/memory-provenance/v1-model-inference.md` → `FF9A8F2E7B29B051F432B02D5803D6612B457C481C17308B69D53B8806042E08`
  - `tests/fixtures/memory-provenance/v1-user-approved.md` → `C13A02A3110D50669B967EF920FB1F88C2035C16E93DF419F7BB4CCC1DF969E5`
  - `docs/ARCHITECTURE.md` → `EFECCDC5BAF1D94120FF21BBE24587B8A8F01F53182BB23BDD6271AD9B6519D7`
  - `tests/evals/results/br007-full-suite.log` → `70A8A4BF489D7113FFE6842531395B708DFAB8ED18D020CECED7341A311E9832`
- Bilinen sınırlar / risk: Mevcut kasadaki notlar otomatik taşınmıyor; taşıma bilinçli olarak isteğe bağlıdır ve kullanıcı verisini kendiliğinden değiştirmez. Günlük özetin `source_sha256` değeri özet metninin bütünlüğünü kanıtlar, ham dökümün içeriğini değil: ham döküm varsayılan olarak saklanmaz. Frontmatter okuyucusu küçük, satır tabanlı bir YAML alt kümesidir; iç içe YAML yapılarını çözmez. Tam paket logunda bir CLI reddi testinden gelen `--wsl-worker` stderr satırı vardır; sonuç `OK (skipped=15)` ve çıkış 0. Gerçek kullanıcı kasası okunmadı/yazılmadı; ham döküm, secret ve özel not gövdesi kanıta konmadı.
- Sonuç: **uygulandı; odak, komşu regresyon ve tam paket testleriyle doğrulandı**.

### BR-008 · Decision Lifecycle — TAMAMLANDI
- Tarih/saat: 2026-11-03 (Europe/Istanbul)
- Sürüm/temel commit: `ac9a3ee` (BR-007 sonrası)
- Değişen dosyalar:
  - `src/respected_brain/memory/decisions.py` (yeni)
  - `src/respected_brain/memory/events.py`
  - `src/respected_brain/integrations/mcp/server.py`
  - `src/respected_brain/integrations/mcp/tools.py`
  - `tests/memory/test_br008_decision_lifecycle.py` (yeni)
  - `docs/ROADMAP-EXECUTION.md`
- Uygulama:
  - Yaşam döngüsü mevcut append-only olay günlüğünden türetilir; ayrı bir kalıcı karar deposu eklenmez. `Decisions.md` yalnızca projeksiyondur ve olay kayıtlarını değiştirmez.
  - Karar satırındaki isteğe bağlı işaretler: `[key: ...]`, `[supersedes: ...]`, `[valid_from: YYYY-MM-DD]`, `[valid_until: YYYY-MM-DD]`; `konu`/`subject` ve `yerine`/`supersedes` eş anlamlıları kabul edilir. İşaretsiz eski kararlar okunmaya devam eder.
  - `active`, `superseded`, `disputed` durumları; açık yerine geçme eski kaydı `superseded/explicit` yapar, `superseded_by` bağlantısı korunur. Geçerlilik süresi dolan kayıt `superseded/validity-expired` olur; kayıt tarihi ile geçerlilik tarihi ayrı alanlardır.
  - Aynı `key` altında çelişen aktif kararlar sessizce birleştirilmez: tümü `disputed` olur ve `conflicting-decisions` nedeniyle insan incelemesine düşer. Çözülemeyen `supersedes` referansı `unresolved-supersedes` olarak incelemeye gider.
  - Her kayıt kaynak agent, oturum, kayıt zamanı, `user_authored`/`model_inference` kökeni ve `pending` inceleme durumunu taşır; BR-007 provenance alanlarıyla çelişmez.
  - `events.project_companion` güncel/geçmiş/inceleme bölümleriyle `🔮 850-Companion/Decisions.md` yazar. MCP `respected_get_decisions` güncel kararları ve inceleme listesini her zaman, geçmişi yalnızca `include_history: true` ile döndürür; `respected_get_companion_context` `Decisions` bölümünü içerir.
- Testler ve komut:
  - `python -m unittest tests.memory.test_br008_decision_lifecycle` → 7 test OK
  - `python -m unittest discover -s tests/memory -t .` → 195 test OK, 2 skip
  - `python -m unittest tests.integrations.test_mcp_and_features` → 34 test OK
  - `python -m unittest discover -s tests -t .` → 978 test OK, 15 skip (`br008-full.log`, yerel/ignore)
  - Not: MCP argüman doğrulaması `boolean` tipini tanımıyordu; `include_history` reddediliyordu. Doğrulama boolean için genişletildi, odak ve tam paket yeniden koşuldu.
- Kabul eşlemesi:
  - Express → Fastify: ikinci oturumda `[key: web-framework] [supersedes: web-framework]` güncel karar Fastify; geçmiş sorgusu Express'i `superseded/explicit` ve `superseded_by` bağlantısıyla buluyor.
  - Yeni oturum güncel kararı getiriyor: MCP varsayılan yanıtı yalnızca aktif Fastify kararını içeriyor.
  - Eski karar silinmiyor: olay günlüğü ve geçmiş projeksiyonu korunuyor; `include_history` ile erişilebiliyor.
  - Çelişki sessiz birleşmiyor: aynı anahtarda Postgres/SQLite testi iki kaydı da `disputed` ve inceleme nedeniyle işaretliyor.
  - Geçerlilik tarihi ile kayıt tarihi ayrı; süre dolumu testi tarihi koruyarak `validity-expired` veriyor.
- Artefaktlar (yol → sha256):
  - `src/respected_brain/memory/decisions.py` → `A206186013DF872D7C0E116244B3724F131008003D2D226CADCD18333BCCB5C1`
  - `src/respected_brain/memory/events.py` → `38CD9122EE5948EAA654AED3621522328B8E719F329A4EA443710823FC4A4FB8`
  - `src/respected_brain/integrations/mcp/server.py` → `2E67BE30714B4B1C6D304D74C5CFBD7F0EB200A1984EC25CFD4A2E188795E787`
  - `src/respected_brain/integrations/mcp/tools.py` → `91B1B68BA1FAAA2DF5E15BF8CE04191AE31AF14A83AF23AAF21C475ADBDD2C2F`
  - `tests/memory/test_br008_decision_lifecycle.py` → `64C286657E78F43FA24CDE13F02A26CCB5F60E01EAE39411286C57EB559A2616`
  - `br008-full.log` → `DC2FFBD9F9DEDBE3DB9F450E7DB466D2C391594C0A115A0A8D1A2BD4E6C46FD6` (commit edilmez, `.gitignore`)
- Bilinen sınırlar / risk: Yaşam döngüsü yalnızca `decisions` alanındaki metin işaretlerinden türetilir; serbest metinli kararlar otomatik olarak anahtarlanmaz ve çelişki tespiti `key` yoksa yapılmaz. `supersedes` eşleşmesi kimlik, anahtar veya normalize metin üzerinden yapılır; çok kısa (4 karakterden az) referanslar metin eşleşmesine girmez. İnceleme durumu `pending` olarak başlar; BR-009 onay/ret akışını ekleyene kadar otomatik `approved` yapılmaz. Projeksiyon her çağrıda tüm olaylardan yeniden hesaplanır; çok büyük günlüklerde maliyet artabilir. Gerçek kullanıcı kasası okunmadı/yazılmadı; ham döküm, secret ve özel not gövdesi kanıta konmadı.
- Sonuç: **uygulandı; odak, komşu regresyon ve tam paket testleriyle doğrulandı**.

### BR-009 · Memory Review & Promotion — TAMAMLANDI
- Tarih/saat: 2026-11-03 (Europe/Istanbul)
- Sürüm/temel commit: `3b7f6f2` (BR-008 sonrası)
- Değişen dosyalar:
  - `src/respected_brain/memory/review.py` (yeni)
  - `src/respected_brain/memory/inbox.py`
  - `src/respected_brain/rpp/memory_workspace.py`
  - `src/respected_brain/rpp/server.py`
  - `tests/memory/test_br009_review.py` (yeni)
  - `docs/ROADMAP-EXECUTION.md`
- Uygulama:
  - `🔮 850-Companion/Inbox` altındaki `review_status: pending` notları kuyruğa alınır; eski `review: pending` alanı da okunur. `memory.review.queue` varsayılan olarak ertelenenleri gizler, `include_deferred: true` ile gösterir.
  - Kullanıcı işlemleri `memory.review.apply` üzerinden yürür: `accept`, `reject`, `correct`, `defer`. İsteğe bağlı `reason`, düzeltmede `corrected_title`/`corrected_body`, ertelemede `until` kabul edilir.
  - `accept` ve `correct` notu `🧠 500-Knowledge/Reviewed/` altına yeni dosya olarak yükseltir; var olan dosya ezilmez. Kalıcı not `review_status: approved`, `origin: user_approved`, `promoted_from` ve `promoted_at` taşır. Düzeltmede gövde ve `source_sha256` güncellenir.
  - `reject` kalıcı bilgi üretmez; not `rejected` olur ve ret parmak izi `memory-review/ledger.jsonl` dosyasına yazılır. Aynı başlık+gövde yeniden önerilirse `REJECTED_REPROPOSAL` ile engellenir; aynı başlık farklı gövdeyle gelirse `review_reason: repeated-rejection` ve `learning_candidate: true` ile işaretlenir. İkinci ret ledger'da öğrenim adayı olarak da işaretlenir.
  - Defter yalnızca eylem, yol, önce/sonra SHA-256, parmak izi, sınırlı neden ve işlem kimliği tutar; not gövdesi, ham döküm veya secret yazmaz. Her işlem kullanıcı incelemesi olarak `reviewed_by: user` ile izlenir.
  - Model kendi kaydını inceleyemez: `reviewer` yalnızca `user` olabilir; aksi halde `MODEL_REVIEW_FORBIDDEN`. MCP'nin `confidence: verified` değerini düşürmesi ve provenance'ın model kaydını `approved` yazmayı reddetmesi korunur.
- Testler ve komut:
  - `python -m unittest tests.memory.test_br009_review` → 6 test OK
  - `python -m unittest discover -s tests/memory -t .` → 201 test OK, 2 skip
  - `python -m unittest discover -s tests/rpp -t .` → 99 test OK, 1 skip
  - `python -m unittest tests.integrations.test_mcp_and_features tests.rpp.test_memory_write` → 39 test OK
  - `python -m unittest discover -s tests -t .` → 984 test OK, 15 skip (`br009-full.log`, yerel/ignore)
  - İlk odak koşusunda ret parmak izi not gövdesindeki `# başlık` satırı yüzünden yeniden öneriyle eşleşmedi; parmak izi başlık satırını normalize edecek şekilde düzeltildi, testler yeniden koşuldu.
- Kabul eşlemesi:
  - Onaylanmamış içerik kalıcı kullanıcı kuralına dönüşmüyor: yalnızca `accept`/`correct` Knowledge altına yazıyor; `reject` ve `defer` yazmıyor.
  - Kabul ve düzeltme izlenebilir: defterde eylem, önce/sonra hash, yükseltilen yol ve kullanıcı damgası var; notta `promoted_to`/`promoted_from` bağlantısı bulunuyor.
  - Model kendi kaydını `verified`/`approved` yapamıyor; inceleme yalnızca açık kullanıcı eylemiyle yürüyor.
  - Reddedilen içerik aynen yeniden önerilemiyor; tekrarlanan başlıklar öğrenim adayı olarak işaretleniyor.
- Artefaktlar (yol → sha256):
  - `src/respected_brain/memory/review.py` → `B8B26EB80AE4361D1D4EEB13F9CB06C3D1DE3C4EDC3C5BF6D24D836B39E1BBD5`
  - `src/respected_brain/memory/inbox.py` → `85F17E836094EFEBE000943C74FED6E307F18B50C6992145F18FBD6B6A51A87C`
  - `src/respected_brain/rpp/memory_workspace.py` → `189D42BEF1B1C7544419BA969C9A01781D12717AE8C41E31B7E454E7C25311C0`
  - `src/respected_brain/rpp/server.py` → `20A613C7E2EA552FE2B962A8A2F41C1DBE1544E056E51B16B7FED214C306D91C`
  - `tests/memory/test_br009_review.py` → `66ADF91452E721875B9666DFCDEDCD8F726A257CDE0F8BEB8F766B829D4D1A17`
  - `br009-full.log` → `8BDA60D1FD5A173397736F545128AA26B308ECEFB09B52D13818CB58EF227171` (commit edilmez, `.gitignore`)
- Bilinen sınırlar / risk: Kuyruk yalnızca `🔮 850-Companion/Inbox` altını tarar; `📥 000-Inbox/Dump` ve eski `unreviewed` notlar otomatik kuyruğa girmez. Ret kontrolü başlık+gövde parmak izine dayanır; anlamca aynı ama yeniden yazılmış önerileri yakalamaz. Öğrenim adaylığı başlık tekrarına dayalı basit bir sezgidir; semantik kümeleme yapmaz. Yükseltme dosya adı tarih+slug+parmak izinin ilk 8 karakteridir; aynı gün aynı başlık/gövde ikinci kez onaylanırsa mevcut içerikle eşleşiyorsa yeniden kullanılır, farklıysa `PROMOTION_CONFLICT` verir. Defter sınırsız büyüyebilir (okuma son 5000 satırla sınırlı); arşivleme/rotasyon yok. Gerçek kullanıcı kasası okunmadı/yazılmadı; ham döküm, secret ve özel not gövdesi kanıta konmadı.
- Sonuç: **uygulandı; odak, komşu regresyon ve tam paket testleriyle doğrulandı**.

### BR-010 · Index Freshness — TAMAMLANDI
- Tarih/saat: 2026-11-03 (Europe/Istanbul)
- Sürüm/temel commit: `0.1.0-beta.1`, `0a5ed0b` (BR-009 sonrası)
- Değişen dosyalar:
  - `src/respected_brain/search/engine.py`
  - `src/respected_brain/rpp/memory.py`
  - `tests/search/test_br010_freshness.py` (yeni)
  - `tests/vault/test_feature_boundaries.py`
  - `docs/ROADMAP-EXECUTION.md`
- Uygulama:
  - `SearchEngine.search(..., freshness="auto")` yeni varsayılanı sorgu öncesinde `index_state()` ile yalnızca mtime taraması yapar; indeks eskiyse mevcut artımlı `index_vault()` çalışır. `freshness="off"` hızlı yol ister.
  - Dönen her isabetin diskteki SHA-256 değeri `files_meta` kaydıyla karşılaştırılır. Uyuşmazlıkta artımlı tazeleme bir kez denenir ve sorgu yeniden koşulur; hâlâ eski olan isabetler sonuçtan çıkarılır. Böylece değişen/silinen notun eski metni güvenilir sonuç olarak dönmez.
  - Tazeleme `writer_lease` ile 1 saniye bekler; başka yazıcı sürüyorsa `BusyError` yutulur ve isabet doğrulaması devralır. `SearchEngine` kurulumu eşzamanlı açılışlarda 10 saniyeye kadar bekler.
  - Salt-okuma motoru yazmadığı için isabet doğrulamasını yapar ve eski isabetleri sonuçtan çıkarır. RPP recall kendi hash denetimi ve `dropped`/`dropped_stale` sayaçlarını korumak için `freshness="off"` ile ham indeks satırlarını alır.
  - Silinen satırlar mevcut `_index_vault` temizliğiyle düşer; indeks dosyası silinip yeniden oluşturulduğunda içerik yalnızca notlardan kurulur.
- Testler ve komut:
  - `python -m unittest tests.search.test_br010_freshness -v` → 8 test OK
  - `python -m unittest discover -s tests/search -t .` → 26 test OK
  - `python -m unittest tests.vault.test_feature_boundaries tests.rpp.test_memory tests.rpp.test_memory_index tests.rpp.test_memory_workspace tests.rpp.test_memory_semantic` → 54 test OK, 1 skip
  - `python -m unittest tests.integrations.test_mcp_and_features` → dahil, OK
  - `python -m unittest discover -s tests -t .` → 992 test OK, 15 skip (`br010-full.log`, yerel/ignore)
- Kabul eşlemesi:
  - Dışarıdan değişen not kısa sürede yeni sürümüyle bulunuyor: sorgu öncesi tazelik ve isabet hash doğrulaması; dış düzenleme testte el ile yeniden indeksleme olmadan yeni terimle bulunuyor.
  - Eski sürüm güvenilir sonuç gibi dönmüyor: değişen içerik, aynı mtime korunsa bile hash uyuşmazlığıyla ayıklanıyor; silinen not hiç dönmüyor; salt-okuma yolunda da eski isabet filtreleniyor.
  - Mevcut artımlı altyapı kullanılıyor: yeni tarama/indeksleme kodu yok; `index_state` + `_index_vault` + `files_meta.sha256` yeniden kullanıldı.
  - Çoklu yazıcı ve dosya kilidi: eşzamanlı `index_vault`/`search` iş parçacıkları ve kilit tutulurken arama testleri geçiyor; kilit sırasında eski metin dönmüyor.
  - Yeniden kurulabilirlik: `search_index.db` silindikten sonra yeni motor sorguyla indeksi notlardan kuruyor.
- Artefaktlar (yol → sha256):
  - `src/respected_brain/search/engine.py` → `CBE00ED9C330EA4BD47C23F9BB48091ECD5DEA1C996E1BD39A3D9BA9F5E01BEC`
  - `src/respected_brain/rpp/memory.py` → `2E7B5F06494CD731CF2091129842AE6165ABDEE8B6E896AF7664C68CBFFC8D8D`
  - `tests/search/test_br010_freshness.py` → `EF6C96B28B4DDE6910444615D9110DEE20426A41DCBC64A60C73F8879A733D4E`
  - `tests/vault/test_feature_boundaries.py` → `A70C21CBBB20461FFFDA74BE373526B38BF2A4B7BC076C4611D60B4B96B28680`
  - `br010-full.log` → `9DBAA58D8A402FCFCF8E620C6EC5DFD9AA669283F4C42318EA5CE4BBCC945754` (commit edilmez, `.gitignore`)
- Bilinen sınırlar / risk: Tazelik taraması mtime tabanlıdır ve `max_files=5000` ile sınırlıdır; üstünde durum `unknown` olur ve ön tarama yapılmaz (isabet doğrulaması yine korur). Mtime'ı korunmuş bir dosyada tamamen yeni bir terim eklenirse ve sorgu eski içerikle eşleşmiyorsa terim bir sonraki tam/artımlı indekslemeye kadar görünmeyebilir. Hash doğrulaması yalnızca dönen isabetler içindir, tüm kasa taranmaz. Dosya sistemi bildirimi/watcher yoktur; tazelik sorgu anında kontrollü taramayla sağlanır. Eşzamanlılık testi aynı süreçte iş parçacıkları ve dosya kilidiyle yapıldı; ayrı süreçlerde yarış testi yok. Gerçek kullanıcı kasası üzerinde ölçüm yapılmadı; ham döküm veya özel not gövdesi kanıta konmadı.
- Sonuç: **uygulandı; odak, komşu regresyon ve tam paket testleriyle doğrulandı**.

### BR-011 · Retrieval Quality — TAMAMLANDI
- Tarih/saat: 2026-11-03 (Europe/Istanbul)
- Sürüm/temel commit: `0.1.0-beta.1`, `2df9b47` (BR-010 sonrası)
- Değişen dosyalar:
  - `src/respected_brain/search/engine.py`
  - `src/respected_brain/search/semantic.py`
  - `tests/search/test_br011_retrieval_quality.py` (yeni)
  - `tests/evals/results/br011-retrieval.json` (yeni)
  - `tests/evals/results/br011-retrieval.md` (yeni)
  - `docs/ARCHITECTURE.md`
  - `docs/ROADMAP-EXECUTION.md`
- Uygulama:
  - Uzun not gövdesi 1200 karakterlik parça sınırıyla paragraf sınırlarından bölünür; her parça ayrı FTS satırıdır. Kısa not tek satır kalır; parçalar `rel_path` ile not başlığına bağlıdır.
  - Sorgu terimlerinin en az üçte birini taşımayan FTS satırı elenir; böylece tek kelimelik OR gürültüsü sonuca girmiyor.
  - Sıralama deterministiktir: normalize BM25 alaka + 0,25 yakınlık + 0,12 güven + eski-yol cezası. `review_status: approved` ve `origin: user_approved|user_authored` öne, `rejected` geriye, geçerliliği dolmuş `valid_until` kararı geriye düşer; yolu `old`, `previous`, `archived`, `deprecated`, `superseded`, `eski`, `onceki` içeren not ceza alır.
  - Aynı yol ve aynı başlık+parça bir kez döner; `limit` dolunca sıralama kesilir. FTS aday havuzu `max(limit*8, 50)` ile sınırlıdır.
  - `files_meta` şemasına `trust` kolonu eklendi; eski şema algılanınca FTS ve meta satırları silinip notlardan okunabilir yeniden kurulum yapılır.
  - Semantik isabetler 0,25 kosinüs eşiğinin altında elenir. Sağlayıcı hatasında `auto`/`hybrid` FTS5'e düşer; açık `semantic` modu hatayı korur.
- Testler ve komut:
  - `python -m unittest tests.search.test_br011_retrieval_quality -v` → 8 test OK
  - `python -m unittest tests.search tests.integrations.test_mcp_and_features tests.rpp tests.vault.test_feature_boundaries tests.evals` → 45 test OK
  - `python -m unittest discover -s tests -t .` → 1000 test OK, 15 skip (`br011-full.log`, yerel/ignore)
  - `python -m tests.evals.harness --modes none,fts,hybrid --repeats 2 --json-out tests/evals/results/br011-retrieval.json --md-out tests/evals/results/br011-retrieval.md` → 50 senaryo, 2 tekrar; `fts` iki tekrarda da %94,0 (stdev 0,0)
- Sonuç (FTS, benchmark):
  - Pass %94,0 (başlangıç %64,0); Hit@1 %92,9 (başlangıç %57,1); Hit@5 %100; MRR 0,964 (başlangıç 0,786); cevap %100; kaynak kapsamı %100; eski-not-üstte 0 (başlangıç 10); bilinmeyen-sorgu %100; P50 30,53 ms, P95 36,98 ms.
  - Kategori: recall 12/12, multi_session 10/10, temporal 7/10, update 10/10, unknown 8/8.
- Kabul eşlemesi:
  - Doğru kaynağı bulma başlangıcın altına inmiyor: pass, Hit@1 ve MRR belirgin yükseldi; Hit@5 %100 korunuyor.
  - Eski karar yeni kararın önüne hatalı geçmiyor: `stale_above_current` 10 → 0; update kategorisi 10/10. `valid_until`, `supersedes` ve güven sinyalleri sıralamaya katılıyor.
  - Uzun notların anlamlı parçalara ayrılması: 1200 karakterlik paragraf sınırlı parçalama; odak testleri uzun notun bölündüğünü ve doğru parçanın bulunduğunu doğruluyor.
  - Tekrarlı sonuçların azaltılması: yol ve başlık+parça tekilleştirmesi; aynı not farklı parçalardan tek kez dönüyor.
  - `active` kararlar ve güvenilir kaynakların öne çıkarılması: onay/güven artısı, reddedilen ve süresi dolmuş kayıt cezası; testlerle sabitlendi.
  - Semantik hatasında güvenli FTS5 fallback: mevcut `auto`/`hybrid` düşüşü korunuyor; eşik altı isabetler eleniyor.
  - Hız ve doğruluğun birlikte ölçülmesi: P50 30,53 ms / P95 36,98 ms, önceki baseline 40,86/53,8 ms'den hızlı.
- Artefaktlar (yol → sha256):
  - `src/respected_brain/search/engine.py` → `0EA20A130D5BD036AEB1D71CA9BD685DC0558F37CAF1D6E31D38D59332F53031`
  - `src/respected_brain/search/semantic.py` → `AF3463FEA87BF24051DCA0D7D2F8D07E03F51BBAC402D37D4E6C2D4EFEF5E3AC`
  - `tests/search/test_br011_retrieval_quality.py` → `FE4795C5C3E2A4D8D9074BE9C8EE8BCFC08060CF6CC9AEF2F78792EF3F93C1FC`
  - `tests/evals/results/br011-retrieval.json` → `7EF864476F9C0CE78D04FFB50DDD9FD423D09BC28EE39DDFD75842C7C959F5B5`
  - `tests/evals/results/br011-retrieval.md` → `D0E99E0548DD46E24746D13712BB337EC5FC96E389280FA01B3A4783F701508B`
  - `br011-full.log` → yerel/ignore, commit edilmedi
- Bilinen sınırlar / risk: Semantik/hibrit kip yerel model etkin olmadığı için ölçülemedi (`SEMANTIC_OFF`); karşılaştırma yalnızca `none` ve `fts` üzerinde. Kalan FTS hataları T01, T02 ve T07: beklenen güncel kaynak ilk sırada değil; bu senaryolar zaman ifadesi ve dosya adı çıkarımına dayanıyor. Güven ve eski-yol sinyalleri sezgiseldir; yolu istemeden `old`/`eski` içeren meşru not ceza alabilir. Parçalama düz metin paragraf sınırlarına dayanır; çok uzun tek paragraf cümle ortasından bölünebilir. Şema yükseltmesi ilk açılışta tam yeniden indeksleme ister. Gerçek kullanıcı kasası üzerinde ölçüm yapılmadı; ham döküm veya özel not gövdesi kanıta konmadı.
- Sonuç: **uygulandı; odak, komşu regresyon ve tam paket testleriyle doğrulandı**.

### BR-012 · Progressive Memory Retrieval — TAMAMLANDI
- Tarih/saat: 2026-11-03 (Europe/Istanbul)
- Sürüm/temel commit: `0.1.0-beta.1` (`0.1.0b1`), `6ccba93` (BR-011 sonrası)
- Değişen dosyalar:
  - `src/respected_brain/memory/context.py` (yeni)
  - `src/respected_brain/integrations/mcp/tools.py`
  - `src/respected_brain/integrations/mcp/server.py`
  - `tests/memory/test_br012_progressive_context.py` (yeni)
  - `tests/evals/progressive.py` (yeni)
  - `tests/evals/results/br012-progressive.json` (yeni)
  - `tests/evals/results/br012-progressive.md` (yeni)
  - `docs/ARCHITECTURE.md`
  - `docs/ROADMAP-EXECUTION.md`
- Uygulama:
  - `memory.context.build_context` sıralı arama sonuçlarını token bütçeli, kısa görev bağlamına çevirir. Varsayılan bütçe 600, üst sınır 4000 token; `detail=short` yalnızca başlık/yol, `summary` odaklı parça döndürür. Bütçe dolunca düşük sıralı sonuç düşer, uzun parçalar kelime sınırında kırpılır ve `truncated`, `tokens`, `items`, `expand` alanları raporlanır.
  - MCP `respected_recall` aracı görev metni, bütçe, sonuç sayısı, ayrıntı ve kategori alır; mevcut FTS sıralamasını kullanır. Tam not gövdesi döndürmez, dönen yol `respected_get_note` ile açılır.
  - Mevcut MCP yazma izinleri, kasa sınırları ve araç görünürlüğü değişmedi. Her mesaja otomatik hafıza ekleme yapılmaz; bağlam yalnızca çağrıldığında üretilir.
  - `tests/evals/progressive.py`, cevap taşıyan notları en az 3000 karakterlik ilgisiz metinle doldurup `search`, `full`, `compact-600`, `compact-120`, `compact-60` görünümlerini aynı 50 senaryoda karşılaştırır.
- Testler ve komutlar:
  - `python -m unittest tests.memory.test_br012_progressive_context` → 10 test OK
  - `python -m unittest discover -s tests/memory -t .` → 211 test OK, 2 skip
  - `python -m unittest discover -s tests/integrations -t .` → 216 test OK
  - `python -m unittest discover -s tests/evals -t .` → 36 test OK
  - `python -m unittest discover -s tests -t .` → 1010 test OK, 15 skip (`br012-full.log`, yerel/ignore)
  - `python -m tests.evals.progressive --json-out tests/evals/results/br012-progressive.json --md-out tests/evals/results/br012-progressive.md` → 50 senaryo; veri kümesi sha256 `c0cdb91c5e9960da32e09dbdefdd1a574790c2e06d6cfd419bb85b402c60e662`
- Sonuç (benchmark):
  - `full`: pass %98,0; Hit@1 %97,6; Hit@5 %100; MRR 0,988; cevap %100; eski-not-üstte 0; ortalama 1103,458 token.
  - `compact-600` ve `compact-120`: aynı doğruluk; ortalama 47,452 token (tam not görünümünün yaklaşık 0,04 katı); cevap %100.
  - `compact-60`: pass %80,0; cevap %78,6; ortalama 29,186 token. Aşırı dar bütçe alt sınır olarak kaydedildi.
  - Kalan senaryo hatası: `T01`.
- Kabul eşlemesi:
  - Aynı görevlerde eşit/daha iyi doğruluk: `compact-600` ve `compact-120`, `full` ile aynı pass/Hit@1/Hit@5/MRR/cevap değerlerini koruyor.
  - Daha az gereksiz hafıza metni: ortalama bağlam maliyeti 1103,458 → 47,452 token; uzun not gövdesi yerine odaklı parça dönüyor.
  - Kısa sonuç → kaynak özeti → tam not akışı: `respected_recall` başlık/yol ve özet parça veriyor; tam gövde `respected_get_note` ile ayrıca isteniyor.
  - Görev bazlı ve token bütçeli bağlam: `task`, `budget_tokens`, `detail`, `limit` ve `category` girdileri odak testleriyle doğrulandı.
  - Mevcut MCP erişim sınırları korunuyor: araç görünürlüğü ve yazma izinleri değişmedi; komşu MCP testleri geçti.
  - Her mesaja tam hafıza eklememe kararı korunuyor: yeni akış istek üzerine çalışıyor, oturum/mesaj kancası eklenmedi.
- Artefaktlar (yol → sha256):
  - `src/respected_brain/memory/context.py` → `FBB7D48FAD9138A55630182E38FF08672C55D76BC3183FAD01567A37B41DB0C6`
  - `src/respected_brain/integrations/mcp/tools.py` → `2087ADA6E5EF8D123509F96B212D712F600CE7A48E2387CAAAC209C9236328CD`
  - `src/respected_brain/integrations/mcp/server.py` → `6D822748951AD7B4B4DB86A208F01ACC7C92CDE9A9636681759D2A1CFA1C3A6B`
  - `tests/memory/test_br012_progressive_context.py` → `C7D05253F49A487727616CA000B677185D34AE4B6EE4A1ACABD892887A4E7F50`
  - `tests/evals/progressive.py` → `4E303ABD96D7A38AF39CAE94371F411B1369D619C921EBCAB170920A62C3149D`
  - `tests/evals/results/br012-progressive.json` → `A0A3BDFDB39684FB7D3100641D20210B4D80CDA123FAC4A5C1F1C45FF425B694`
  - `tests/evals/results/br012-progressive.md` → `9618C1BF68D35F67C05BB786CE1B51F13DC5D964BE859B67526DBCCC23C67896`
  - `docs/ARCHITECTURE.md` → `E17AA4298497CB73D14B028167C02BEFD2C56F0AB727A6BC222A88C666AADD59`
  - `br012-focus.log`, `br012-neighbor-*.log`, `br012-full.log` → yerel/ignore, commit edilmedi
- Bilinen sınırlar / risk: Token tahmini karakter/4'tür; gerçek model tokenizasyonu farklı olabilir. `compact-60` cevap terimlerini kırptığı için doğruluk düşüyor; varsayılan 600 bu nedenle korunuyor. Semantik/hibrit görünümler yerel model olmadan ölçülmedi. Benchmark sentetiktir ve gerçek kullanıcı kasası okunmadı; ham not gövdesi, döküm veya secret kanıta konmadı. `T01` bilinen sıralama hatası olarak kaldı.
- Sonuç: **uygulandı; odak, komşu regresyon, benchmark ve tam paket testleriyle doğrulandı**.

### BR-013 · Memory Poisoning & Privacy Tests — TAMAMLANDI
- Tarih/saat: 2026-11-03 (Europe/Istanbul)
- Sürüm/temel commit: `0.1.0-beta.1` (`0.1.0b1`), `267f858` (BR-012 sonrası)
- Değişen dosyalar:
  - `src/respected_brain/memory/untrusted.py` (yeni): talimat görünümlü satırları `[UNTRUSTED_DATA]` önekiyle işaretler.
  - `src/respected_brain/memory/redact.py`: düz metin `ad is değer` / iyelik (`şifrem değer`) ve sorgu dizesi sırları; kısa bearer/basic.
  - `src/respected_brain/memory/flush.py`, `src/respected_brain/memory/compile.py`, `src/respected_brain/briefing/service.py`: dış metni model istemine girmeden önce inert işaretle.
  - `src/respected_brain/integrations/mcp/server.py`: yazma izni etkin kasa ve kayıtlı kasaya çözülen yol ile sınırlandı.
  - `tests/memory/test_untrusted_input.py` (yeni), `tests/memory/test_redact.py`, `tests/memory/test_transcript_integrity.py`,
    `tests/integrations/test_mcp_and_features.py`, `tests/scenarios/test_regression_matrix.py`.
  - `docs/ARCHITECTURE.md`: gizlilik ve güven sınırı davranışı güncellendi.
- Komutlar ve sonuçlar:
  - `python -m unittest tests.memory.test_redact tests.memory.test_untrusted_input tests.memory.test_session_scripts tests.memory.test_transcript_integrity tests.integrations.test_mcp_and_features tests.scenarios.test_regression_matrix` → 181 test OK, 2 skip
  - `python -m unittest tests.evals.test_summarization_eval tests.memory.test_redact` → 22 test OK (maskelenmiş değerin ikinci kez maskelenmesi düzeltildikten sonra)
  - `python -m unittest discover -s tests -t .` → 1018 test OK, 15 skip (`br013-full.log`, yerel/ignore)
- Kabul eşlemesi:
  - Zararlı README, web sayfası, döküm ve not örnekleri: Scenario 21 metni README ve web anlık görüntüsünden okuyup Threads/daily üzerinden istem üreticilerine veriyor; döküm ve not örnekleri `test_untrusted_input` ile kapsanıyor.
  - Dış metnin kalıcı kullanıcı talimatına dönüşmemesi: talimat görünümlü satırlar üç istem yolunda da `[UNTRUSTED_DATA]` taşıyor; Threads.md ve config/kurallar diskte değişmiyor.
  - Secret maskeleme genişletmesi: düz metin parola/iyelik ve sorgu dizesi örnekleri, kısa basic kimlik bilgisi ve arşiv kopyası test edildi; maskelenmiş değer idempotent.
  - MCP izinsiz yazma, yetki iptali, kasa değişimi: yazma aracının görünmemesi, izin iptalinde iz bırakmaması ve eski sunucunun yeni etkin kasaya yazamaması test edildi.
  - Arşiv açık/kapalı ve saklama süresi: varsayılan kopyalamama, açıkken maskeli kopya, kasa dışı konum ve süre sonunda silme test edildi.
  - Saldırı regresyonu: Scenario 21 yayın öncesi regresyon matrisine eklendi.
- Artefaktlar (yol → sha256):
  - `src/respected_brain/memory/untrusted.py` → `CEE5CFBE44A0919F5708139BE87FB746696516DCF42DA0CF1EF983F3985C3EBB`
  - `src/respected_brain/memory/redact.py` → `5AD7B382A3CF87A5AC5483619200F5DDAB7CDEF7783D82D09185FD0259834C77`
  - `src/respected_brain/memory/flush.py` → `17B0E49A4D7EEE9171E261F7EC9F11BF55E5CFFA6ABA0AF8585F76654BA131F7`
  - `src/respected_brain/memory/compile.py` → `E017438C8BF7F98E8DC242BCC6405E74F4796C101B98EFDB05BAB4042FE5F989`
  - `src/respected_brain/briefing/service.py` → `E1EBD8BDA17E7131B31DDF3EEECB7F4DBED0EC05F33F813DA3E153EDDCF48B9E`
  - `src/respected_brain/integrations/mcp/server.py` → `E46E440601F18A6DF07E87226D70FD12930BA9D9687E35B7A43D6236D248ABC0`
  - `tests/memory/test_untrusted_input.py` → `1DAB963BB30DC4B99EACCD53664DE9DA371F7022AE1440D548F0798489EF50E6`
  - `tests/memory/test_redact.py` → `396DB22D8B27D6C390B4467ABB79E7F6ACD12C4C35C79B48A28582D9E590E437`
  - `tests/memory/test_transcript_integrity.py` → `C11AB3FB0C0810958D23DD0EA40BA5E0EC47BEA35D084821737D2BB692AA3C8E`
  - `tests/integrations/test_mcp_and_features.py` → `D8A516D145D7326DA8244D5268F47757B2C169CF7444EBDF450911198DD31A0A`
  - `tests/scenarios/test_regression_matrix.py` → `0E37B291DB888C943EB2936309F995128926E35CB02095479512A74E399745B1`
  - `docs/ARCHITECTURE.md` → `2B40D21AB6B665B1486BC02EEAAB92BF5EA641CDEEE31ACEBF4A612CAF339793`
  - `br013-full.log` → yerel/ignore, commit edilmedi
- Bilinen sınırlar / risk: Inert işaretleme kalıp tabanlıdır; talimat görünümü taşımayan ikna edici metin modeli yönlendirebilir. Maskeleme bilinen kalıplarla sınırlıdır; yeni/rastgele sır biçimleri kaçabilir. Arşiv kapalıyken kopya oluşturulmaz ama sağlayıcının kendi dökümü silinmez. Testler sentetik metin kullanır; gerçek kullanıcı kasası, dökümü veya sırrı okunmadı ve kanıta konmadı.
- Sonuç: **uygulandı; odak, komşu regresyon ve tam paket testleriyle doğrulandı**.

<!-- EVIDENCE:END -->
