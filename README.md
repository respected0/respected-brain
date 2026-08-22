# 🧠 avenoxbeyin v2: hatırlamayı unutmayan ikinci beyin

[Obsidian](https://obsidian.md) + [Claude Code](https://claude.com/claude-code) üstünde çalışan,
açık kaynak bir **ikinci beyin**. Yerel bir Markdown vault, kalıcı hafıza, sıfır bağımlılık,
sıfır ekstra ücret. Dosya yönetmezsin, konuşursun.

**v1'in tezi devamlılıktı: oturum açılınca geçen oturum bağlama giriyordu.** İşe yarıyordu ama tek
bir kırılgan varsayıma dayanıyordu: modelin oturum biterken hafıza dosyalarını güncellemeyi
hatırlaması. Hatırlamadığı her seferde o gün kayboluyordu. **v2'nin tezi şu: hafıza rica değil,
mekanizmadır.** Artık oturum kapanışını bir kanca yakalıyor, konuşmayı arka planda özetleyip
`daily/` altına günlük log olarak yazıyor, akşamları günde bir kez bir derleyici o logları
`knowledge/` altında birbirine bağlanan makalelere dönüştürüyor. Ertesi sabah bu bilgi tabanının
indeksi kendiliğinden bağlama giriyor. Kimsenin bir şey yazmayı hatırlaması gerekmiyor.

Video izlemene gerek yok, kurulum videosu da yok. Aşağıdaki tek satırı yapıştır, kurulumu Claude
Code'un kendisi yapar.

---

## Hızlı başlangıç

Terminalde `claude` çalıştır ve şunu yapıştır:

```
Read https://avenox.lol/beyin.md and follow it exactly to build my second brain.
```

Ya da repoyu doğrudan klonla, üç komut:

```bash
git clone https://github.com/avenoxai/avenoxbeyin.git
cd avenoxbeyin
claude "Read SETUP.md and follow it exactly to set up my second brain from this template."
```

Claude birkaç soru sorar (adın, ne iş yaptığın, AI ortağının adı), vault'u kurar, kancaları bağlar,
masaüstüne 🧠 ikonlu bir kısayol koyar.

### Zaten v1 beynin varsa

Aynı komut yeter. `SETUP.md` önce mevcut bir beyin arar, bulursa yükseltme moduna geçer.
Yükseltme **sadece ekler**: mevcut hafıza dosyalarına, Dashboard'a, notlarına dokunulmaz. Sadece
`daily/`, `knowledge/`, scriptler ve skill'ler eklenir, dört kanca dosyası yenisiyle değiştirilir,
`settings.json` kanca kaydı tekrar tekrar çalıştırılabilecek şekilde birleştirilir. İlk adım
vault'un git anlık görüntüsünü almaktır, yani geri dönüş her zaman açıktır.

---

## v1 → v2

| | v1 | v2 |
| --- | --- | --- |
| Günlük hafıza | model hatırlarsa yazar | oturum kapanışında **otomatik** yazılır |
| Kanca sayısı | 3 | 4 (`PreCompact` eklendi) |
| Compaction | konuşma sıkıştırılınca kaybolur | sıkıştırma öncesi yakalanır |
| Bilgi tabanı | yok | `knowledge/` altında derlenmiş, birbirine bağlı makaleler |
| Oturum başı bağlam | son oturum + threadler | + kurallar, son journal, bilgi indeksi, bugünün logu |
| Kalıcı kurallar | yok | `Kurallar.md`, "bunu böyle yapma" dediğinde oraya yazılır |
| Sağlık kontrolü | yok | `beyin doktor` skill'i, tek tabloda tanı |
| Eski geçmiş | yok | `geçmiş import`: ChatGPT, Claude, Gemini dışa aktarımları |
| Yükseltme | yok | yerinde, ekleme yapan, tekrar çalıştırılabilir |
| Bağımlılık | bash | bash + python3 (ikisi de sistemde var) |

---

## Mimari

```
   oturum biter                    konuşma sıkışmak üzere
   (SessionEnd)                         (PreCompact)
        |                                    |
        v                                    v
  session-end.sh                       pre-compact.sh
        |                                    |
        +------------------+-----------------+
                           v
                       flush.py           (claude -p --model haiku)
                  transkripti okur, Türkçe özet çıkarır
                           v
                 daily/YYYY-MM-DD.md      <-- makine yazar, sen değil
                           |
        (saat 18'den sonra, günde bir kez, değişen log varsa)
                           v
                      compile.py          (claude -p --model sonnet)
                           v
   knowledge/concepts/*.md + knowledge/connections/*.md + knowledge/index.md
                           |
                           v
                   session-start.sh
        indeksi + bugünün logunu + hafızayı bir sonraki oturuma enjekte eder
```

Yazma tarafı makineye ait, ilişki katmanı sana ait: ortağın hâlâ `Last-Session.md` ve `Threads.md`
dosyalarını kendi eliyle günceller. Makine katmanı onun yerine geçmez, altını doldurur.

## Ne alıyorsun

```
{Ad}OS/
├── 📥 000-Inbox/Dump/        # ham yakalama
├── 🎯 100-Command-Center/    # Dashboard
├── 🏰 300-Projects/          # proje başına bir klasör
├── 🧠 500-Knowledge/         # insanın yazdığı notlar
├── 🛠️ 600-Arsenal/           # araçlar, kişiler, kaynaklar
├── 🔮 850-Companion/         # ortağın kalıcı hafızası (+ Kurallar.md)
├── daily/                    # makine yazar: günlük loglar
├── knowledge/                # makine derler: makaleler + bağlantılar + indeks
├── 📦 900-Archive/
├── 📋 Templates/
└── .claude/                  # kancalar, scriptler, skill'ler (süreklilik motoru)
```

- **İsmini sen koyduğun bir AI ortağı.** Varsayılan dili Türkçe.
- **Süreklilik motoru.** Dört sıfır bağımlılıklı kanca, her açılışta hafızayı bağlama koyar, her
  kapanışta oturumu diske yazar.
- **Dosya tabanlı hafıza.** API anahtarı yok, ücretli servis yok, her şey senin diskinde.
- **Opsiyonel semantik hafıza.** [mem0](https://mem0.ai) ücretsiz katmanı üstüne anlamsal arama
  ekler, temel sürümü tamamen ücretsiz ve kredi kartı istemez. İstemezsen sistem eksiksiz çalışır.
- **Tek tık başlatıcı.** Masaüstünde 🧠 ikonlu bir uygulama vault'u anında açar.

## Maliyet, dürüst hâliyle

Ekstra ücret yok; arka plan özetleyici ve derleyici mevcut Claude aboneliğinin günlük limitinden
küçük bir pay kullanır (özet: her oturum sonunda küçük bir Haiku çağrısı; derleme: günde bir
Sonnet çağrısı).

## Gereksinimler

- macOS (masaüstü kısayolu ve ikonu macOS araçlarını kullanır; vault'un kendisi platform bağımsız)
- Linux destekli, Windows için WSL önerilir
- [Claude Code](https://claude.com/claude-code), [Obsidian](https://obsidian.md), `python3`
  (macOS'ta Command Line Tools ile gelir)

## Bir şey ters giderse

Vault klasöründe `claude` açıp `beyin doktor` yaz. Kancalar, scriptler, python3, `claude` CLI,
günlük log tazeliği, son derleme durumu, iCloud çakışma dosyaları ve git durumu tek tabloda gelir,
her kırmızı satırın altında düzeltme komutu yazar.

---

## Credits

Bilgi derleme mimarisi Andrej Karpathy'nin LLM bilgi tabanı desenine dayanır:
https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f

Geri kalanı [Avenox](https://avenox.lol) günlük kullandığı sistemden, kişisel veriden arındırılıp
herkes için genelleştirilerek çıkarıldı.

## Lisans

MIT, [LICENSE](LICENSE) dosyasına bak. PR'lar açık.

---

## In English (short version)

**avenoxbeyin** is an open-source AI second brain: an Obsidian vault driven by Claude Code, with
memory that survives across sessions. v1 gave you continuity but depended on the model remembering
to write its memory files. v2's thesis is that **memory must be a mechanism, not a discipline**: a
`SessionEnd` and a `PreCompact` hook flush every conversation into `daily/` logs automatically via
a small background Haiku call, and once a day a Sonnet compile pass turns those logs into linked
articles under `knowledge/`. The next session starts with that knowledge index already in context.

Install: `git clone https://github.com/avenoxai/avenoxbeyin.git && cd avenoxbeyin && claude "Read
SETUP.md and follow it exactly to set up my second brain from this template."` Already running v1?
The same command detects it and upgrades in place: additive only, your memory files are never
touched, the settings merge is idempotent, and it snapshots the vault with git before it starts.

No extra cost: everything runs on your existing Claude subscription through `claude -p`. No API
keys, no paid services, bash and python3 stdlib only. Knowledge-compilation architecture credit:
Andrej Karpathy's LLM knowledge base pattern,
https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f. MIT licensed.
