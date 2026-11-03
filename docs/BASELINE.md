# Respected Brain — Baseline Raporu (M0 / BR-003)

Bu belge, mevcut sürümün hafıza kalitesi için sabitlenmiş başlangıç noktasıdır.
Sonraki her hafıza değişikliği aynı veri seti ve aynı komutla ölçülür.

- Sürüm: `0.1.0-beta.1` (`0.1.0b1`)
- Ölçüm tarihi: 2026-10-30 (Europe/Istanbul)
- Veri seti: `tests/evals/scenarios.json`, 50 senaryo
- Veri seti sha256: `C0CDB91C5E9960DA32E09DBDEFDD1A574790C2E06D6CFD419BB85B402C60E662`
- Makine okunur rapor: `tests/evals/results/baseline-0.1.0-beta.1.json`
- İnsan okunur rapor: `tests/evals/results/baseline-0.1.0-beta.1.md`

## Yeniden üretim

```powershell
# respected-brain/ içinde
python -m tests.evals.harness --modes none,fts,hybrid --repeats 3 `
  --json-out tests/evals/results/baseline-0.1.0-beta.1.json `
  --md-out tests/evals/results/baseline-0.1.0-beta.1.md
```

Aynı fixture, sürüm ve ayarla iki çalıştırma birebir aynı senaryo skorlarını verdi
(FTS pass `%64.0`; iki koşuda aggregate ve tüm senaryo skorları eşit).

## Sonuçlar

| Mod | Pass | Hit@1 | Hit@5 | MRR | Cevap | Kapsam | Eski not üstte | Bilinmeyen | P50 ms | P95 ms | Bağlam token |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `none` | 16.0% | 0.0% | 0.0% | 0.000 | 0.0% | 0.0% | 0 | 100.0% | n/a | n/a | 0.0 |
| `fts` | 64.0% | 57.1% | 100.0% | 0.786 | 100.0% | 100.0% | 10 | 100.0% | 40.86 | 53.8 | 18.606 |
| `hybrid` | n/a | n/a | n/a | n/a | n/a | n/a | 0 | n/a | n/a | n/a | n/a |

`hybrid` bu makinede `unavailable` (`SEMANTIC_OFF`): yerel semantik sağlayıcı etkin değil.
Semantik/hibrit ölçümü sağlayıcı açıldığında aynı komutla alınmalıdır; sıfır sonuç gibi raporlanmaz.

## Kategori kırılımı (FTS)

| Kategori | Senaryo | Başarılı | Başarısız | Pass |
|---|---|---|---|---|
| recall | 12 | 12 | 0 | 100% |
| multi_session | 10 | 10 | 0 | 100% |
| temporal | 10 | 2 | 8 | 20% |
| update | 10 | 0 | 10 | 0% |
| unknown | 8 | 8 | 0 | 100% |
| **Toplam** | **50** | **32** | **18** | **64%** |

Başarısız yakalamaların tamamı iki sınıfta toplanıyor:

- **temporal:** doğru kaynak Hit@5 içinde ama beklenen güncel kaynak ilk sırada değil.
- **update:** eski not güncel notun üstünde (`stale_above_current=1`); 10/10 senaryoda.

Bu iki sınıf M2 (BR-008) ve M3 (BR-011) işlerinin hedefidir. Gerçek agent oturumundan
yakalama başarısı bu baseline'da ölçülmedi; BR-004 entegrasyon matrisi ile ölçülecek.

## Sürüm karşılaştırması

Yeni bir rapor üretildikten sonra:

```powershell
python -m tests.evals.compare `
  tests/evals/results/baseline-0.1.0-beta.1.json `
  tests/evals/results/yeni-rapor.json --json-out tests/evals/results/karsilastirma.json
```

Araç aynı veri seti sha256'sını doğrular; pass/Hit@1/Hit@5/MRR/cevap/kapsam/bilinmeyen
düşüşünü, eski-not-üstte artışını ve P50/P95'te %30'u aşan gecikmeyi gerileme sayar
(çıkış kodu `1`). Veri seti değişirse karşılaştırmayı reddeder (`2`).

## Bilinen sınırlar

- Sonuçlar sentetik fixture'lara aittir; gerçek kullanıcı kasası kullanılmadı.
- `semantic`/`hybrid` bu ortamda çalıştırılamadı.
- P50/P95 tek makine ölçümüdür; CI gürültüsü için %30 tolerans sabittir.
- Gerçek agent oturum yakalama ve özetleme kalitesi kapsam dışı (BR-004, BR-006).