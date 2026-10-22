# Brain mimarisi

Programın nasıl kurulduğu, verinin nerede durduğu, başka ürünlerin hafızaya nasıl eriştiği ve hangi güvenlik
sınırlarının uygulandığı. Kullanım: [USAGE.md](USAGE.md). Komutlar: [COMMANDS.md](COMMANDS.md). Üç ürünün ortak
kuralları (kurucu, komutlar, ayarlar, protokol) [PRODUCT_CONTRACT.md](PRODUCT_CONTRACT.md) dosyasındadır; burada
tekrarlanmaz.

## 1. Üç ayrı kök

| Kök | Windows | macOS | Linux | İçerik |
|---|---|---|---|---|
| Program | `%LOCALAPPDATA%\Respected\RespectedBrain\app` | `~/Applications/RespectedBrain.app` | `~/.local/lib/respected-brain` | `respected-brain.exe`, `app/` (çalışma ortamı ve `resources/`), `distribution.json`, kaldırıcı |
| Veri | `%LOCALAPPDATA%\Respected\RespectedBrain\data` | `~/Library/Application Support/RespectedBrain` | `$XDG_DATA_HOME/respected-brain` | `config.json`, `install-manifest.json`, `logs/`, `backups/`, `vaults/<UUID>/{state,cache,overrides}` |
| Kasa | kişinin seçtiği yer (varsayılan `Belgeler\RespectedOS`) | aynı | aynı | notlar, `.obsidian/`, `.respected.json` |

- Kökler birbirini içeremez. Windows'ta yollar Known Folders ile çözülür (yönlendirilmiş Belgeler/AppData dahil).
- `RESPECTED_APP_DIR` + `RESPECTED_DATA_DIR` iki kökü birlikte değiştirir; testler ve geliştirme bunu kullanır.
- Kasada program dosyası, arama veritabanı, kaldırıcı ya da AI aracı ayarı bulunmaz. `.respected.json` yalnızca kasanın
  kalıcı UUID'sini ve şema sürümünü taşır; makineye özgü yollar veri kökündeki `config.json`'dadır.
- Program salt okunur bir yerde çalışabilir; program köküne hiçbir şey yazılmaz.

## 2. Modüller

| Modül | Sorumluluk |
|---|---|
| `__main__.py`, `cli.py` | Giriş noktası, argümanlar, JSON çıktı ve hata biçimi |
| `bootstrap.py`, `core/` | Kökler, UUID bağlamı, ayar deposu, kilitler, platform, paket kaynaklarına erişim |
| `settings.py` | Kişinin ayarlarının tek şeması; `config`, RPP `settings.*` ve kurucunun `--set`'i bunu kullanır |
| `vault/` | Kasa kaydı, seçimi, not ve beceri haritaları |
| `providers/` | AI araçlarının komut satırını çalıştırma, çıktıyı normalleştirme, yedek araca geçme |
| `memory/` | Döküm özetleme, `daily` yazımı, derleme, olay günlüğü, asistan bağlamı, maskeleme |
| `briefing/` | Sabah özeti |
| `search/` | FTS5 araması, dizin tazeliği, isteğe bağlı yerel anlamsal arama |
| `integrations/` | AI aracı hook'ları ve uyarlayıcıları, Claude/Codex yerel eklenti paketi (`plugin.py`: `DataRoot/vaults/<UUID>/plugin`), MCP sunucusu, bağlantı kaydı, zamanlayıcı, değişiklik farkı |
| `installation/` | `setup`, `repair`, `uninstall`, ayar değişikliğinde yeniden yapılandırma, sahiplik kaydı, işlem günlüğü |
| `rpp/` | RPP sunucusu: ayarlar, bağlantı planı, hafıza izinleri, arama, yazma, dizin, anlamsal arama |
| `maintenance/` | Kasa denetimi ve onarımı, içe alma, Restic ve Git yedekleri |
| `resources/` | Değişmez paket içeriği: varsayılanlar, talimatlar, beceriler, araç şablonları, kasa şablonu |

Sınırlar: `core` özellik modüllerini içe aktarmaz; özellikler `cli`'yi içe aktarmaz; içe aktarma sırasında klasör
oluşturulmaz, süreç başlatılmaz. `vault` program kurmaz; `providers` kasa temizlemez; `search` veritabanını kasaya yazmaz;
`installation` not içeriğini program dosyası saymaz; `resources` canlı ayar ya da durum değildir.

## 3. Hafıza döngüsü

1. Oturum başlarken hook ilişkili notları, haritaları ve sınırlı bir bağlamı AI aracına verir.
2. Tur, sıkıştırma ve kapanış olaylarında döküm ortak biçime çevrilir; arka planda `flush` modelden özet alır.
3. Geçerli özet, oturum ve araç kimliğiyle `daily` dosyasındaki yönetilen bloğa kilit altında yazılır. Aynı oturumun
   tekrar yazılmasını kasa UUID'sine bağlı durum dosyaları önler.
4. Derleyici günlüklerden `knowledge` notları üretir: model çıktısı geçici bir alanda hazırlanır, yalnızca izinli yollar,
   kaynak ve hedef hash'i ile eşzamanlı değişiklik denetiminden sonra atomik olarak aktarılır. Oturum kapanışındaki
   otomatik derleme yalnızca tamamlanmış önceki günleri alır.
5. Zamanlayıcı açıksa sabah görevi derleme ve özet üretir.

Biçim denetimleri özetin doğru olduğunu kanıtlamaz; model çıktısıdır.

## 4. Kurulum, sahiplik ve geri alma

- **Program dosyaları kurucunundur.** `setup` ve `repair` kurulu programı `distribution.json`'daki SHA-256 değerleriyle
  doğrular; bozuk dosyayı kendileri düzeltmez, kurucunun yeniden çalıştırılmasını ister. Ürün kurulumunu
  `data\install-manifest.json`'a kaydeder; `manifest`'in `install_state` değeri bu kayıttan ve dosyaların şimdiki
  hash'inden gelir (`installed` / `repair-needed`).
- **Kasa şablonu yalnızca yeni ve boş kasaya bir kez uygulanır.** Dolu ama kayıtlı olmayan bir klasöre hiçbir şey yazılmaz;
  onarım ve güncelleme mevcut notları şablonla yenilemez. `📋 Templates`, `.obsidian` ve `🔮 850-Companion` dosyaları
  kopyalandıktan sonra kişinindir.
- **Talimatlar ve beceriler pakettedir** (`resources/`). AI araçlarına yazılırken kasa kimliği ve ad gibi tercihler
  eklenir. Kişinin değiştirdiği talimat ve beceriler `vaults/<UUID>/overrides/` altında tutulur ve paketin önüne geçer.
- **Dış değişiklikler kayıtlıdır.** AI araçlarının ayar dosyalarına, zamanlayıcıya ve kısayola yapılan her değişiklik bir
  işlem günlüğüyle (yedek, kilit, karşılaştır-ve-değiştir, aşamalar) yapılır; yarıda kalan işlem `recover` ile ya da
  bir sonraki işlemde geri alınır. Sahiplik kaydı dosyaların kopyasını değil, **farkı** tutar: JSON için değişen anahtarlar
  ve liste öğeleri, diğer dosyalar için satır işlemleri, artı SHA-256 parmak izleri. Geri alma bu farkı dosyanın şimdiki
  haline uygular: ürünün girdileri gider, aracın sonradan yaptığı ve kişinin eklediği değişiklikler kalır. Kişinin
  değiştirdiği bir girdi çakışma olarak bildirilir, dokunulmaz. Böylece başka bir aracın `~/.claude.json` içindeki
  sırrı ürünün kayıtlarına ya da yedeklerine girmez (işlem bitince günlükler de aynı biçimde sıkıştırılır).
- **Ayar değişikliği bir işlemdir.** `config set` bağlantıları, adları ya da sabah özeti saatini değiştirince
  (`installation/reconfigure.py`) ürün kendi dış kayıtlarını aynı işlemde günceller; hata olursa ikisi birlikte geri alınır.
- **Kaldırma** yalnızca kayıtla eşleşen girdileri kaldırır, kurulum kaydını her zaman siler, `--purge` ile veri kökünü de
  siler; kasaya hiçbir durumda dokunmaz.

## 5. Başka ürünlerin hafızaya erişimi

Orchestrator gibi başka bir ürün hafızaya yalnızca **izinle** ve yalnızca `rpp` üzerinden erişir; Brain'in kodunu
içe aktarmaz.

- **İzin bir sırdır, ad değil.** `memory.grant {label, write?, max_results?}` bir izin kimliği ve bir kez gösterilen bir
  anahtar döner; veri kökünde (`memory-grants.json`) yalnızca anahtarın SHA-256'sı saklanır. En fazla 20 etkin izin.
  Yanlış, eksik ve iptal edilmiş anahtar aynı `PERMISSION_DENIED` yanıtını alır. İzin oluşturulduğu kasaya bağlıdır;
  etkin kasa değişince geçersizleşir. `memory.revoke` izni kapatır. Orchestrator bunu `memory connect` ile yapar.
- **`memory.recall` salt okunurdur.** Dizini SQLite `mode=ro` ile açar, yazıcı kilidi almaz, dosya oluşturmaz, dizini
  kurmaz ya da onarmaz. Kasa her zaman etkin kayıtlı kasadır; istekte yol, kasa ya da `host` alanı `BAD_REQUEST`'tir.
  Bir sonuç yalnızca notun şimdiki SHA-256'sı dizinlendiği andakine eşitse döner (silinen ya da değişen notun eski metni
  sızmaz; bunlar `dropped` ve `dropped_stale` sayılarında görünür). Sınırlar: sorgu 1–200 karakter ve en fazla 12 terim,
  en fazla 20 sonuç, parça 40–400 karakter; not gövdesinin tamamı dönmez.
- **Dizin güncelliği.** Dizini ürünün kendi süreçleri artımlı olarak tazeler: `index-refresh`, her AI oturumu başında
  başlayan arka plan `flush --maybe-compile`, her `flush` sonu, sabah görevi ve her `memory.write` sonrası. Dosya izleyici
  yoktur: oturum dışında düzenlenen bir not bir sonraki oturumda ya da günlük görevde dizine girer.
  `memory.index.refresh` yalnızca `{confirm: true}` ve işlem kimliğiyle çalışır; Hub kullanır, Orchestrator'ın izni yetmez.
- **`memory.write` (yazma izniyle).** Not her zaman **yeni** bir dosya olarak `🔮 850-Companion/Inbox/Orchestrator/` altına
  yazılır (var olan dosyaya ya da istenen yola asla); ön bilgide kaynak, izin ve işlem kimliği vardır; en fazla 500 not;
  aynı işlem kimliği aynı içerikle tekrarlanırsa ilk sonuç döner. `memory.write.revert` yalnızca bu iznin yazdığı ve
  değişmemiş notu siler.
- **Anlamsal arama (isteğe bağlı).** `memory.semantic.pull {confirm}` sabitlenmiş bir llama.cpp `llama-server` (Windows x64)
  ve bge-m3 modelini (Q4_K_M, MIT lisanslı, Türkçe dahil çok dilli) veri kökündeki `semantic-runtime/` klasörüne indirir;
  boyut ve SHA-256 doğrulanır, arşivden yol kaçışı reddedilir. Sunucu yalnızca bir işlem için boş bir yerel porta
  başlatılır ve sonra kapatılır; sürekli çalışan süreç yoktur. Yerel olmayan bir uç nokta reddedilir; tek ağ kullanımı bu
  indirmedir. Vektörler FTS dizininin yanındaki `semantic_index.db`'dedir (not başına bir vektör: başlık + ilk 2000
  karakter). `memory.recall` `mode` alanı `auto` (hazırsa karma, değilse FTS), `fts`, `semantic`, `hybrid` olabilir;
  sağlayıcı sorunu FTS'ye düşer. Her sorgu sunucuyu başlatır (bu makinede 2,6–4,2 sn).
- **Hub'ın Hafıza sayfası** `memory.search`, `memory.note.read`, `memory.capture.*`, `memory.briefing.run` işlemlerini
  Hub'ın kendi yerel komutlarıyla çağırır; Hub'ın web görünümü `memory.*` işlemlerini doğrudan çağıramaz.
- **Her istemde otomatik hafıza eklemek bilinçli olarak yapılmadı.** Hafıza AI araçlarına oturum başında, MCP ile ve
  istendiğinde ulaşır; her mesaja not eklemek her mesajda kasa metnini modele gönderir.

## 6. Gizlilik

- **MCP ile not yazma bir izindir** (`mcp_write`, varsayılan kapalı, her çağrıda yeniden okunur). Kapalıyken yazma araçları
  listelenmez. Açıkken notlar yalnızca `🔮 850-Companion/Inbox/MCP` altına, var olanın üzerine yazmadan, `source: mcp` ve
  `review: pending` ön bilgisiyle gider; `confidence: verified` `inferred` olarak saklanır (model kendine kefil olamaz).
  Hiçbir not seçilmiş klasörlere kendiliğinden taşınmaz.
- **Dökümler varsayılan olarak saklanmaz.** `archive_transcripts` açıksa döküm kasaya değil veri kökündeki
  `session-archive/` klasörüne, maskelenmiş olarak yazılır ve `transcript_retention_days` sonra silinir.
  `capture_mode = manual` hiçbir şey kopyalamaz.
- **Maskeleme** (`memory/redact.py`): özel anahtar blokları, JWT, bearer/basic kimlik bilgileri, sağlayıcı anahtarları
  (OpenAI, Anthropic, GitHub, Hugging Face, Slack, AWS, Google, npm), adreslerdeki kimlik bilgileri ve adı sır olduğunu
  söyleyen `ad = değer` çiftleri (İngilizce ve Türkçe) özetleyiciye gitmeden, `daily`'ye yazılmadan ve arşivlenmeden önce
  ayıklanır. Düz metinle yazılmış bir parola tanınmaz.
- Özet isteğindeki veri sınırlayıcıları her istekte rastgele bir kod taşır; döküm veri bloğunu kapatamaz.

## 7. Güvenlik sınırları

**AI araçlarını çalıştırma** (`providers/runner.py`): argüman listesiyle, kabuk olmadan; izin atlayan bayraklar
(`--dangerously-skip-permissions`, `--yolo` gibi) üretilmez. Süreç Windows Job Object / POSIX süreç grubuyla, kopmuş alt
süreçler dahil sonlandırılır. Bu, aracın kendi izinlerinin yerine geçen bir işletim sistemi kum havuzu değildir.

| Araç | Metin modu | Çalışma alanı modu |
|---|---|---|
| Claude | `--safe-mode --tools ""` | `--safe-mode`, `Read,Write,Edit,Glob,Grep`, `acceptEdits` |
| Codex | `--sandbox read-only` | `--sandbox workspace-write` |
| Antigravity | `--sandbox` | `--sandbox --add-dir . --mode accept-edits` |
| Cursor | desteklenmez, reddedilir | `--output-format text` |
| Gemini | `--sandbox --approval-mode plan` | `--sandbox --approval-mode auto_edit` |

`RESPECTED_LLM_COMMAND` ile verilen özel komut, doğrulanmış bir yalıtım olmadığı için başlatılmadan reddedilir
(`custom-isolation-required`). Model metni beş zorunlu Türkçe bölüm ve yapısal denetimlerle sınırlanır; bu, istem
enjeksiyonunu tümüyle çözmez. Döküm, web içeriği ve model yanıtı yalnızca veridir, talimat sayılmaz.

**Derleme:** geçici alanda hazırlanır; sembolik bağ ve yeniden ayrıştırma noktası, yol kaçışı, izinsiz silme ve değişiklik
durdurulur (POSIX'te `0700`).

**Web alımı** (`maintenance/ingestion/url_safety.py`, `defuddle.py`): yalnızca HTTP/HTTPS, izinli portlar ve genel IP'ler;
yerel, özel, link-local, multicast ve ayrılmış adresler reddedilir; karışık IPv4/IPv6 DNS yanıtı reddedilir. Doğrulanan IP'ye
bağlanılır, ikinci DNS sorgusu yapılmaz; TLS ad doğrulaması gerçek adla yapılır; vekil sunucu atlanmaz. Durum, başlık,
yönlendirme, parça çerçevesi ve gövde aynı mutlak süre sınırını paylaşır. İşletim sisteminin `getaddrinfo` çağrısı iptal
edilemez; bu yüzden en fazla iki arka plan çözümleyici kullanılır.

**Git anlık görüntüsü** (`publish_git_snapshot.py`): kişinin index'i kopyalanır (yoksa HEAD, o da yoksa boş ağaç);
kopyalanan bloblar ve `git add -A` ile kurulan ağaç ayrı ayrı sır taramasından geçer; yayınlanan commit tam olarak taranmış
ağaca bağlanır (`commit-tree`). İşlem sırasında index ya da HEAD değişirse hiçbir şey itilmez; itmeden sonra uzak dal
doğrulanmadan makbuz yazılmaz. Raporlarda sırrın kendisi değil yalnızca yolu ve türü yer alır.

**Dağıtım güveni:** kurucu Authenticode ile imzalı değildir. Hub kurucu paketini Ed25519 imzasıyla doğrular; kurulu
program `distribution.json` hash'leriyle doğrulanır (bu bir yayıncı imzası değildir).

## 8. Testler

| Klasör | Kapsam |
|---|---|
| `core/`, `vault/`, `briefing/`, `search/`, `memory/` | bağlam, yollar, kilitler, platform; kasa kaydı ve haritalar; sabah özeti; arama ve dizin tazeliği; özetleme, olaylar, maskeleme |
| `installation/` | `setup`, `repair`, `uninstall`, yeniden yapılandırma, işlem günlüğü, geri alma |
| `integrations/` | AI aracı bağlantıları, hook'lar, MCP, değişiklik farkı, zamanlayıcı, sağlayıcı izinleri |
| `rpp/` | protokol sunucusu, bağlantı planı, hafıza işlemleri ve izinleri |
| `maintenance/`, `security/` | bakım araçları, Restic, Git anlık görüntüsü, sır taraması; ağ güvenliği, girdi sınırları |
| `packaging/` | paket sözleşmesi, dondurulmuş dağıtım, kurucu |
| `scenarios/` | çapraz senaryolar, sağlayıcı ve saldırı matrisleri |
| `native/` | fiziksel paket smoke'u (geçici köklerde) ve WSL köprüsü; elle ya da CI'da paketle çalışır |
| `support/` | ortak sahteler (test değil) |

`tests/__init__.py` her çalıştırmada HOME, USERPROFILE, APPDATA ve LOCALAPPDATA'yı geçici klasöre yönlendirir; hiçbir test
gerçek AI aracı ayarına ya da kasaya ulaşamaz. `dist/` yoksa dağıtım testi yerelde atlanır; CI önce derler ve testi zorunlu
tutar. CI (Windows): Python 3.10 uyumluluk alt kümesi; Python 3.13 ile dondurulmuş derleme, Python'suz başlatma ve fiziksel
smoke; tam test takımı.

Neyin neyi kanıtladığı ayrıdır: birim testleri arayüz davranışını, dağıtım testi dondurulmuş programı, fiziksel smoke
geçici köklerde kurulum/güncelleme/kaldırmayı kanıtlar. Hiçbiri gerçek bir sağlayıcı oturumunu ya da her işletim
sistemini kanıtlamaz. Hub tarafındaki uçtan uca testler gerçek kurucuyu kullanır (`respected-hub/README.md`).

## 9. Açık sınırlar

| Konu | Durum |
|---|---|
| Kod imzası (Authenticode) | yok; SmartScreen uyarır |
| macOS, Linux, WSL | kod ve betikler var; derlenmez, CI'da test edilmez |
| Gemini CLI, Cursor | yalnızca test verileriyle; Claude Code, Codex ve Antigravity gerçek oturumla sınandı (Windows). Codex eklenti hook'ları kişinin onayından (`/hooks`) sonra çalışır ve içerik değişince onay düşer |
| Boşluklu program yolu | Codex ve Antigravity hook komutları tırnaksız olmalı: boşluklu yol Windows'un 8.3 kısa adıyla yazılır. Kısa ad yoksa Codex `& "yol"` biçimine döner, Antigravity (tırnakları yeniden kaçırır) ve WSL profili çalışmaz |
| Dizin anlık değil | oturum dışı düzenlemeler sonraki oturumda ya da günlük görevde dizine girer |
| Hafıza izni | `settings.apply` yapabilen herkes izin oluşturabilir (aynı kullanıcı hesabı) |
| Anlamsal arama | her sorguda sunucu başlar; karma sonuçlarda alaka eşiği yok; yalnızca Windows x64 çalışma ortamı |
