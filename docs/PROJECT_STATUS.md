# 📍 Respected Brain — Proje Durumu

> Aktif durumun tek kaynağı bu belgedir (2026-10-21, sürüm `0.1.0-beta.1`). Geçmiş çalışma kayıtları Git geçmişindedir.

## 1. Ürün

Windows beta. SecondBrain, **Respected Hub** üzerinden kurulan, güncellenen, onarılan ve kaldırılan dondurulmuş bir
programdır (`%LOCALAPPDATA%\Respected\RespectedBrain\app\respectedbrain.exe`); makinede Python gerekmez. Bağımsız
kurucu yoktur. Hub kapalıyken de hook'lar, MCP ve zamanlanmış brifing kurulu programla çalışır.

| Alan | Durum |
| --- | --- |
| Yakalama (hook'lar, `auto`/`manual` capture modu, bekleyenleri şimdi yakala) | var; gerçek Claude Code oturumlarıyla doğrulandı |
| Derleme, günlük, sabah brifingi, Companion hafızası | var |
| Hatırlama: hook bağlamı, MCP, RPP token recall | var |
| Arama: FTS5 her zaman; isteğe bağlı yerel anlamsal arama (llama.cpp + bge-m3, Hub'dan açılır) | var; gerçek modelle doğrulandı |
| Yetkili hafıza yazımı (Orchestrator için ayrı `write` izni, yalnız gelen kutusu, geri alınabilir) | var |
| Hub "Hafıza" çalışma alanı (arama, okuma, hızlı not, brifing) | var |
| Kurulum sihirbazı: Kimlik → Hafıza → Kaynaklar → İzinler, istemci başına seçim | var; masaüstü E2E ile doğrulandı |
| Kaldırma: yalnız sahipli girdileri geri alır, kasa ve notlar kalır | var |
| Restic yedeği ve `--restore-to` | var; gerçek restic ile sınandı |

## 2. Doğrulama

* Testler `tests/` altında `src` ile aynı alanlara bölünmüştür; `python -m unittest discover -s tests -t .` hepsini koşar
  (≈980 test). Test paketi HOME/APPDATA'yı geçici klasöre yönlendirir; gerçek AI istemci ayarına ulaşılamaz.
* CI (Windows): Python 3.10 uyumluluk alt kümesi, 3.13 dondurulmuş build + dağıtım doğrulama + fiziksel paket smoke'u,
  3.10/3.13 tam test matrisi. Ayrıntı: [TEST-MATRIX](TEST-MATRIX.md).

## 3. Açık sınırlar

| Konu | Durum |
| --- | --- |
| Kod imzası (Authenticode) | yok; SmartScreen uyarısı beklenir |
| SLSA yayın kanıtı | yerel/çevrimdışı yayın üretemez; beta paketleri Hub'ın Ed25519 imzasıyla doğrulanır, motorun kanıt kontrolü `--allow-unattested` ile atlanır |
| macOS / Linux / WSL | kod durur, derlenmez ve CI'da test edilmez |
| Codex, Gemini, Cursor, Antigravity gerçek oturumları | yalnız Claude Code gerçek oturumla sınandı; diğerleri fixture'larla |
| İstem anında (prompt-time) otomatik hafıza enjeksiyonu | yok; bilinçli karar, [RPP_MEMORY_RECALL](decisions/RPP_MEMORY_RECALL.md) |

## 4. Çalışma kuralları

[AGENTS.md](../AGENTS.md): canlı kasa ve program değiştirilmez; push sonrasında CI sorgulanarak beklenmez, sonuç
kullanıcı yeniden çağırdığında incelenir; kullanıcı istemedikçe paralel ajan çalıştırılmaz. Bu bilgisayara özel devreye
alma tercihi Git dışındaki `.local/ROLLOUT.md` kaydındadır.
