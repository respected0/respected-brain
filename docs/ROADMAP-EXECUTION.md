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

### [ ] BR-008 · Decision Lifecycle (P0, L)

- `active`, `superseded`, `disputed` durumları.
- Bir kararın başka kararın yerini aldığının gösterilmesi.
- Geçerlilik tarihi ile kayıt tarihinin ayrılması.
- Eski karar geçmişi silinmeden yenisinin güncel sayılması.
- Çelişen kararların sessizce birleştirilmemesi.
- Kritik çelişkilerin insan incelemesine gitmesi.

**Kabul:** Express → Fastify senaryosunda yeni oturum güncel kararı getiriyor; geçmiş sorgusu eski kararı da buluyor.

### [ ] BR-009 · Memory Review & Promotion (P0, M)

- Inbox ve `review: pending` yaklaşımının genişletilmesi.
- Kabul, ret, düzeltme, erteleme işlemleri.
- Tekrarlanan hataların öğrenim adayı işaretlenmesi.
- Modelin kendi kaydını otomatik `verified` yapmasının engellenmesi.
- Onaylanan bilginin yetkili işlemle kalıcı bilgiye yükseltilmesi.
- Reddedilen kaydın yeniden önerilmesinin kontrolü.

**Kabul:** Onaylanmamış içerik kalıcı kullanıcı kuralına dönüşmüyor; kabul/düzeltme izlenebilir.

---

## M3 — Hızlı ve doğru hafıza geri çağırma

### [ ] BR-010 · Index Freshness (P0, M)

- Editörde değişen dosyanın indeks güncelliği.
- Mevcut artımlı indeksleme altyapısının kullanılması.
- Bildirim, kontrollü tarama veya sorgu öncesi tazelik seçenekleri.
- Silinen/değişen dosyanın eski metnini döndürmeme.
- Çoklu yazıcı ve dosya kilidi testleri.
- İndeksin notlardan yeniden kurulabilirliği.

**Kabul:** Dışarıdan değişen not kısa sürede yeni sürümüyle bulunuyor; eski sürüm güvenilir sonuç gibi dönmüyor.

### [ ] BR-011 · Retrieval Quality (P1, L)

- FTS5, semantik, hibrit benchmark karşılaştırması.
- Alaka eşiği ve sıralama stratejisi.
- Uzun notların anlamlı parçalara ayrılması.
- Tekrarlı sonuçların azaltılması.
- `active` kararlar ve güvenilir kaynakların öne çıkarılması.
- Semantik hatasında güvenli FTS5 fallback.
- Hız ve doğruluğun birlikte ölçülmesi.

**Kabul:** Doğru kaynağı bulma başlangıcın altına inmiyor; eski karar yeni kararın önüne hatalı geçmiyor.

### [ ] BR-012 · Progressive Memory Retrieval (P1, M)

- Kısa ve önceliklendirilmiş başlangıç bağlamı.
- Kısa sonuç → kaynak özeti → tam not akışı.
- Görev bazlı ve token bütçeli bağlam.
- Mevcut MCP erişim sınırlarının korunması.
- Görev başarısı ile context maliyetinin birlikte karşılaştırılması.
- Her mesaja tam hafıza eklememe kararının korunması.

**Kabul:** Aynı görevlerde eşit/daha iyi doğruluk, daha az gereksiz hafıza metniyle sağlanıyor.

---

## M4 — Güvenlik ve yayın kalitesi

### [ ] BR-013 · Memory Poisoning & Privacy Tests (P0, M)

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
<!-- EVIDENCE:END -->
