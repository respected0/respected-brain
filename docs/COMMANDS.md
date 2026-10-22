# Brain komutları

Kurulu program: `%LOCALAPPDATA%\Respected\RespectedBrain\app\respected-brain.exe` (PATH'e eklenmez; tam yolu kullanın).
Kaynaktan: `python -m respected_brain`. Linux'ta `~/.local/bin/respected-brain`.

Ortak kurallar (üç ürün aynı, bkz. [PRODUCT_CONTRACT.md](PRODUCT_CONTRACT.md)):

- Çıktı UTF-8 JSON'dur. Hata: `{"error": {"code", "message", "hint"}}`.
- Çıkış kodu: `0` başarı, `1` işlem başarısız, `2` kullanım ya da geçersiz ayar.
- `--version` (`respected-brain <sürüm>`), `--help` ve `<komut> --help` hiçbir şey kurmaz ya da yazmaz.
- Kasa isteyen komutlar `--vault <yol>` ya da `--vault-id <UUID>` alır (ikisi birden olmaz); verilmezse
  `RESPECTED_VAULT_PATH`, o da yoksa etkin kasa kullanılır.
- `hook` ve `mcp` komutlarının stdout'u protokol çıktısıdır; tanı mesajları stderr'e ve `logs/` klasörüne gider.

## Kurulum ve bakım

| Komut | Ne yapar |
|---|---|
| `setup [--vault YOL] [--platform windows-native\|windows-wsl\|posix] [--set A=D]...` | Kurucunun yazdığı programı `distribution.json` ile doğrulayıp kaydeder, boş kasayı bir kez oluşturur, ayarları ve seçilen bağlantıları uygular. Kurucu çalıştırır; elle de çalışır. |
| `repair [--vault YOL \| --vault-id ID]` | Program dosyalarını doğrular (bozuksa kurucuyu yeniden çalıştırmayı söyler), kurulum kaydını ve bağlantıları yeniler. Kapalı bağlantıyı açmaz. |
| `uninstall [--vault-id ID] [--purge]` | Ürünün AI araçlarındaki girdilerini, zamanlanmış görevi, kısayolu ve kurulum kaydını kaldırır. `--purge` ayarları ve çalışma verisini de siler. Program dosyaları kaldırıcınındır; kasa asla silinmez. |
| `recover` | Yarım kalmış işlemleri geri alır; işlemden sonra değişmiş dosyaları korur. |
| `config` | Bütün ayarları gösterir. |
| `config get ANAHTAR` | Bir ayarı gösterir. |
| `config set A=D [A=D...]` | Doğrular ve uygular; geçersizse hiçbir şey yazmaz (çıkış 2). Anahtarlar: [USAGE.md](USAGE.md#6-ayarlar). |
| `health` | Sağlık kontrolü (RPP `health` ile aynı); sağlıklıysa 0. |

## Kasa

| Komut | Ne yapar |
|---|---|
| `vault list` | Kayıtlı kasaları ve UUID'lerini gösterir. |
| `vault register YOL [--new-identity]` | Mevcut bir kasayı kaydeder (kimlik dosyası ve ayarlar yazılabilir). `--new-identity` kopyaya yeni UUID verir. |
| `vault discover YOL` | Klasörde kasa kimliği arar; hiçbir şey kurmaz. |
| `open` | Kasa klasörünü dosya yöneticisinde açar (masaüstü kısayolu bunu çağırır). |
| `maps` | Kasa ve beceri haritalarını üretir (not yazar). |

## Hafıza

| Komut | Ne yapar |
|---|---|
| `search [SORGU] [--limit N] [--category KLASÖR] [--json] [--reindex]` | FTS5 tam metin araması. Sorgusuz: dizin istatistikleri. Dizini yazabilir. |
| `index-refresh` | Arama dizinini (ve açıksa anlamsal vektörleri) artımlı günceller; kasaya yazmaz. Oturum başı/sonu ve günlük görev bunu kendiliğinden yapar. |
| `compile [--before-date YYYY-AA-GG] [--max-calls N] [--dry-run]` | Günlüklerden `knowledge` notlarını model ile derler. `--dry-run` önizlemedir ama kilit ve durum dosyası yazabilir. |
| `briefing` | Zamanı gelmişse günlük derleme ve sabah özetini üretir. |
| `flush` | Bir oturum dökümünü özetleyip `daily`'ye yazar. Hook'ların kullandığı iç komuttur. |
| `hook --provider P --event E` | AI aracının hook giriş noktası (`claude`, `codex`, `cursor`, `antigravity`, `gemini`; olay `start`, `prompt`, `precompact`, `postcompact`, `turn`, `end`, `notify`). Elle çalıştırılmaz. |
| `semantic status\|enable\|disable\|pull [--provider llama\|ollama] [--model M]` | Yerel anlamsal aramayı Hub'sız yönetir: durum, aç/kapat, modeli indir (`pull`, tek ağ kullanan işlem). Hub'ın `memory.semantic.*` işlemleriyle aynı kod. |
| `stats [--days N]` | Oturum başlarında AI araçlarına gönderilen hafıza bağlamının boyutu: oturum sayısı, toplam/ortalama/en çok karakter, tahmini token (yaklaşık 4 karakter). Kayıt `state/context-usage.jsonl`. Tasarruf karşılaştırması yapmaz: bağlamsız bir temel yoktur. |
| `maintenance ARAÇ [argümanlar]` | Bakım aracı (aşağıda). |

**Tanı:** `RESPECTED_HOOK_TRACE=<dosya>` ortam değişkeni ya da veri klasöründeki `hook-trace.txt` (ilk satırı bir dosya yolu) her hook çağrısının girdisini ve çıktısını o dosyaya ekler. AI araçları hook'ları kısıtlı ortamla başlatabildiği için dosya biçimi gerekir; işin bitince dosyayı silin.

## Protokol ve MCP

| Komut | Ne yapar |
|---|---|
| `rpp` | stdin'den bir RPP isteği okur, stdout'a bir yanıt yazar. Hub ve Orchestrator bunu kullanır. |
| `mcp` | AI araçları için stdio MCP sunucusu. |

**RPP işlemleri** (protokol sürümü `"1"`): `manifest`, `health`, `settings.schema|validate|apply|readback`,
`integrations.plan` (bağlantı değişikliğinin salt okunur önizlemesi), `memory.grant|revoke` (başka ürüne hafıza izni),
`memory.recall` (izinle salt okunur arama), `memory.write|write.revert` (izinle gelen kutusuna not), `memory.search`,
`memory.note.read`, `memory.capture.note|run`, `memory.briefing.run`, `memory.index.status|refresh`,
`memory.semantic.status|configure|pull`. Ayrıntı: [ARCHITECTURE.md](ARCHITECTURE.md#5-başka-ürünlerin-hafızaya-erişimi).

**MCP araçları:** `respected_search` (arama), `respected_get_note` (not okuma), `respected_get_decisions` (karar ve kural
notları), `respected_get_companion_context` (asistan bağlamı), `respected_expand` (bağlantıları genişletme). `mcp_write`
açıksa ayrıca `respected_quick_capture` ve `respected_remember` (yalnızca `🔮 850-Companion/Inbox/MCP` altına yeni not) ve
`respected_revert_note` (MCP'nin yazdığı, sizin değiştirmediğiniz notu geri alır). Arama, dizin önbelleğini yazabilir.

## Bakım araçları

| Araç | Ne yapar | Yazar mı |
|---|---|---|
| `vault_linter` | Kırık bağlantıları, yetim notları ve bayatlamış sayfaları bulur | rapor |
| `tiling_check` | Aynı konuyu tekrar eden, birleştirilmesi gereken notları bulur | rapor |
| `architect_scan` | Bir kod projesinin dillerini, modüllerini ve kararlarını tarar | rapor |
| `repair_daily` | `daily` oturum bloklarındaki tekrarları onarır (önce yedek alır) | evet |
| `smart_merge` | İki notu birleştirir, eskisini yenisine yönlendirir | evet |
| `mine_agent_history` | AI araçlarının geçmiş oturumlarını kasaya alır | evet |
| `defuddle` | Bir web sayfasını not olarak alır (yalnızca genel internet adresleri) | evet |
| `backup_restic` | Restic yedeği, doğrulama, `--restore-to` ile geri yükleme | önizleme; `--apply` ile yedekler |
| `publish_git_snapshot` | Kasanın sır taramasından geçmiş Git anlık görüntüsünü iter | önizleme; `--apply` ile commit + push |

Her aracın seçenekleri: `respected-brain maintenance ARAÇ --help`.
