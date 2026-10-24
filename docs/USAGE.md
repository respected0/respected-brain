# Brain kullanım rehberi

Kurulumdan kaldırmaya kadar kişinin yapacağı her şey. Komutların tam listesi [COMMANDS.md](COMMANDS.md), iç yapı
[ARCHITECTURE.md](ARCHITECTURE.md).

## 1. Kurulum (Windows)

`RespectedBrain-Windows-Setup.exe` kullanıcı başına kurulur, yönetici izni istemez, Python gerektirmez. İlk sayfada
iki yol vardır:

- **Respected Hub ile devam et (önerilen):** kurucu en güncel Hub'ı indirip kurar ve Brain'i Hub'ın kurulum
  sayfasında açar. Sorular orada sorulur, kurulumu Hub aynı kurucuyla yapar.
- **Yalnızca Brain:** kurucu sırayla sorar:
  - **Kimlik:** adınız, asistanınızın adı, kısa bir tanıtım. Asistan ve sabah özeti size bu adla hitap eder.
  - **Not kasası:** yeni boş bir klasör ya da daha önce Brain'in kullandığı bir kasa. Dolu ama Brain'e ait
    olmayan bir klasöre şablon yazılmaz.
  - **Bağlantılar:** oturumları hafızaya yakala, hafıza MCP sunucusu, sabah özeti görevi, masaüstü kısayolu.
  - **AI araçları:** yalnızca ilk ikisinden biri açıksa sorulur. Oturumları hangi araçlardan yakalayacağını ve hangi araçların
    hafızayı MCP ile kullanabileceğini seçersin (Hub'daki Kaynaklar ve İzinler listeleriyle aynı). Bilgisayarında bulunan
    araçlar işaretli gelir.

Kurucu, kurmadan önce "bilgisayarınızda neler olur" sayfasını gösterir: kurulumda, kullanırken, güncellemede ve kaldırmada neler yazıldığı, değiştiği ve silindiği. Aynı bilgi Hub'ın Kütüphane sayfasındaki ürün kartında da vardır (`packaging/windows/brain_info.txt`).

Kurucu programı `%LOCALAPPDATA%\Respected\RespectedBrain\app` altına yazar ve ürünün kendi `setup` komutunu çalıştırır:
kasa bir kez oluşturulur, ayarlar yazılır, seçilen bağlantılar kurulur. Bir adım başarısız olursa ürün yaptığı
değişiklikleri geri alır; kurucu yeniden çalıştırılabilir. Yüklü uygulamalar girdisini kurucu yazar.

Sessiz kurulum aynı ayarları anahtarlarla alır (anahtarlar: bölüm 6):

```text
RespectedBrain-Windows-Setup.exe /VERYSILENT /VAULT="D:\Notlar\RespectedOS" /SET=user_name=Ayşe /SET=assistant_name=Jarvis /SET=integrations.mcp=true
```

AI özetleri için kullanmak istediğiniz aracın (Claude Code, Codex, Gemini CLI…) komut satırında oturum açık olmalıdır.
Dosya ve arama işlemleri için gerekmez.

### macOS ve Linux

Kurulum betikleri var ama **doğrulanmadı**. Dağıtımın açılmış klasöründe:

```sh
./setup.sh --vault "$HOME/Documents/RespectedOS" --set assistant_name=Jarvis     # Linux; macOS: ./setup.command
./setup.sh --uninstall [--purge]
```

Program Linux'ta `~/.local/lib/respected-brain`, komut `~/.local/bin/respected-brain`; macOS'ta
`~/Applications/RespectedBrain.app`. Veri Linux'ta `$XDG_DATA_HOME/respected-brain` (yoksa `~/.local/share/respected-brain`),
macOS'ta `~/Library/Application Support/RespectedBrain`.

## 2. Kurucuyu yeniden çalıştırmak

Ürün kuruluyken kurucu tek bir sayfa gösterir:

- **Onar / Güncelle:** program dosyaları bu kurucudaki sürümle yenilenir, ardından `respected-brain repair` kayıtları ve
  bağlantıları doğrular. Ayarlar ve kasa korunur. **Güncelleme budur:** yeni sürümün kurucusunu çalıştırmak (sessiz:
  `/VERYSILENT`). Hub güncellemeyi kendisi önerir ve aynı kurucuyu çalıştırır.
- **Ayarları değiştir:** Kimlik, Bağlantılar ve AI araçları sayfaları mevcut değerlerle açılır; kaydetmek `config set` ile aynıdır.
- **Kaldır:** ürünün kaldırıcısını açar (bölüm 9).

## 3. İlk kontrol

```text
respected-brain --version
respected-brain vault list
respected-brain health
```

Kasayı Obsidian'da klasör olarak açın. `🔮 850-Companion` altında `Core.md` asistanın kimliği ve sizin hakkınızdaki
bağlam, `Kurallar.md` kalıcı çalışma tercihleriniz, `Threads.md` açık konular, `Last-Session.md` son oturumun devir
notudur. Bunları siz düzenlersiniz; program üzerine yazmaz.

Gerçek bir deneme: bağlantısı açık bir AI aracında kısa ve anlamlı bir konuşma yapın, oturum bitince kasanın `daily`
klasöründeki günün dosyasına özetin geldiğini ve konuşmayı doğru anlattığını kontrol edin. İkinci bir araç da
bağlıysa yeni bir oturumda aynı bağlamı aldığına bakın. Özet birkaç saniye ile birkaç dakika arasında gelir; süre
aracın komut satırına, ağa, kotaya bağlıdır.

## 4. Kasa düzeni

| Klasör | İçerik |
|---|---|
| `📥 000-Inbox/Dump` | Ham notlar ve hızlı yakalamalar |
| `🎯 100-Command-Center` | Dashboard, haritalar, sabah özetleri |
| `🏰 300-Projects` | Proje notları |
| `🧠 500-Knowledge` | Sizin yazdığınız kalıcı bilgi |
| `🛠️ 600-Arsenal` | Araç ve kaynak notları |
| `🔮 850-Companion` | Core, Kurallar, Threads, Last-Session, Journal; `Inbox/MCP` ve `Inbox/Orchestrator` AI araçlarının izinle yazdığı notlar |
| `daily` | Oturum özetleri (programın yönettiği bloklar; kendi notlarınız ayrı kalır) |
| `knowledge` | Derlenmiş dizin, kavramlar, bağlantılar, günlük |
| `📋 Templates`, `📦 900-Archive` | Not şablonları, tamamlanan notlar |

Klasör adları programın sözleşmesidir; `🔮 850-Companion` gibi klasörleri yeniden adlandırmayın. Kasanın kendisinin adı
serbesttir. Kasa kökündeki `.respected.json` kasanın kalıcı kimliğini (UUID) taşır; silmeyin.

## 5. Günlük kullanım

- **Hub'da:** Brain → Hafıza sayfasında not arama (tam metin; açıksa anlamsal), not okuma, hızlı not ve "sabah
  özetini şimdi çalıştır".
- **AI aracında:** hook'lar oturum başında bağlam verir, oturum bitince özet yazar. MCP açıksa araç kasada arar ve not
  okur; `mcp_write` açıksa yalnızca gelen kutusuna geri alınabilir not yazar.
- **Komutla:**

```text
respected-brain search "transaction rollback" --json
respected-brain compile --dry-run
respected-brain compile --before-date 2026-10-21
respected-brain briefing
respected-brain open
```

`compile`, `--before-date` verilmezse günün henüz bitmemiş günlüğünü de derleyebilir; oturum kapanışındaki otomatik
derleme yalnızca önceki günleri alır. `briefing`, zamanı gelmişse sabah özetini üretir; derleme adımı başarısız olsa da
özet dosyasını yazıp 1 ile çıkabilir. Bu yüzden dosyanın varlığı her adımın başarılı olduğunu göstermez. Özetler model
çıktısıdır; kararlarınızı doğru yansıttığını kontrol edin.

**Anlamsal arama (isteğe bağlı):** Hub → Brain → Ayarlar → "Anlamsal arama". Onaylarsanız sabitlenmiş bir
llama.cpp çalışma ortamı ve bge-m3 modeli (yaklaşık 460 MB) ürünün veri klasörüne indirilir, her sorguda yerelde çalışır;
notlarınız bilgisayardan çıkmaz. Kapatılınca tam metin araması devam eder.

## 6. Ayarlar

Ayarların tek kaynağı ürünün şemasıdır; kurucu, Hub ve komut aynı doğrulamayı kullanır.

```text
respected-brain config
respected-brain config get briefing_time
respected-brain config set user_name=Ayşe briefing_time=07:30
```

| Anahtar | Ne | Varsayılan |
|---|---|---|
| `user_name` | Adınız; asistan ve sabah özeti size bu adla hitap eder | boş |
| `user_bio` | Kasa şablonunda sizi tanıtan satır | boş |
| `assistant_name` | Asistanın adı; kasadaki kimlik ve AI araçlarına verilen araç adları bunu kullanır | boş |
| `summary_provider` | Özetleyici AI: `auto`, `codex`, `claude`, `antigravity`, `gemini`, `cursor` | `auto` |
| `provider_fallback` | Seçilen araç başarısız olursa diğer kurulu araçları dene | `true` |
| `capture_mode` | `auto`: oturumlar bitince özetlenir; `manual`: yalnızca siz isteyince | `auto` |
| `briefing_time` | Sabah özeti görevinin saati (SS:DD) | `08:00` |
| `mcp_write` | AI araçları MCP ile gelen kutusuna geri alınabilir not yazabilsin | `false` |
| `archive_transcripts` | Oturum dökümlerini gizli bilgileri ayıklanmış olarak kasa dışında sakla | `false` |
| `transcript_retention_days` | Saklanan dökümlerin silinme süresi (1–90 gün) | `14` |
| `integrations.global` | Seçili AI araçlarına hafıza hook'ları, kuralları ve becerileri eklensin | `false` |
| `integrations.clients` | Yakalanan araçlar, virgülle (ör. `claude,codex`); boş: kurulu olanların hepsi | boş |
| `integrations.mcp` | Hafıza AI araçlarına MCP sunucusu olarak sunulsun | `false` |
| `integrations.mcp_clients` | MCP izni olan araçlar; boş: yakalanan araçlarla aynı | boş |
| `integrations.schedule` | İşletim sisteminin zamanlayıcısına günlük sabah özeti görevi | `false` |
| `integrations.shortcut` | Masaüstüne kasayı Obsidian'da açan kısayol (kasanın Obsidian'da bir kez açılmış olması gerekir) | `false` |

Ad, bağlantı ya da sabah özeti saati değişince ürün AI araçlarındaki ve zamanlayıcıdaki kendi kayıtlarını aynı işlemde
günceller. Kapalı bir bağlantıyı onarım ya da güncelleme açmaz.

**Kasa seçimi:** kasa gerektiren komutlarda sıra `--vault <yol>` ya da `--vault-id <UUID>` (ikisi birden olmaz),
`RESPECTED_VAULT_PATH`, sonra ayarlardaki etkin kasadır. Geçersiz bir seçim başka bir kasaya kaymaz. Aynı UUID'ye sahip bir
kopya ayrı kasa olarak kaydedilemez; bilerek yeni kimlik vermek için `vault register <yol> --new-identity`.

**Ortam değişkenleri:** `RESPECTED_APP_DIR` + `RESPECTED_DATA_DIR` program ve veri kökünü birlikte değiştirir (geliştirme
ve test için); `RESPECTED_VAULT_PATH` kasayı seçer. `RESPECTED_LLM_COMMAND` ile özel model komutu çalıştırılmaz: yalıtım
sağlanamadığı için reddedilir.

**Veri klasöründe ne var:** `config.json` (ayarlar, kasa kayıtları), `install-manifest.json` (kurulum ve sahiplik
kaydı; elle düzenlemeyin), `vaults/<UUID>/state` (tekrar önleme ve oturum durumu), `vaults/<UUID>/cache` (arama dizini;
yeniden üretilebilir), `vaults/<UUID>/overrides` (kişisel talimat ve beceri değişiklikleri), `logs/`, `backups/` (işlem
yedekleri).

## 7. AI araçları

| Araç | Yakalama noktası |
|---|---|
| Claude Code | yerel `respected-brain` eklentisi (hook'lar, `Stop`, beceriler); ayarlarda doğrudan hook kalmaz |
| Codex | yerel `respected-brain` eklentisi (hook'lar, beceriler) ve notify köprüsü (mevcut notify zinciriniz korunur) |
| Cursor | hook'lar, `afterAgentResponse` |
| Antigravity | Antigravity/Gemini uyarlayıcısı, `Stop` |
| Gemini CLI | hook'lar, `AfterAgent` |

Eklenti paketi veri klasöründe durur ve kaldırınca silinir. Kurulum ve onarım sonunda `claude plugin marketplace add`/`install` ve
`codex plugin add` komutlarını da çalıştırır (araç yoksa atlanır, başarısızlık kurulumu bozmaz). Claude'da eklentiye eklentiler bölümünden izin verilir; Codex eklenti hook'larını kurulumda ve
içerikleri değiştiğinde ayrıca onaylatır (`/hooks`). Onaylanmadan çalışmazlar, onayı Brain vermez; sonra AI aracı yeniden başlatılır.

Claude Code, Codex ve Antigravity gerçek oturumlarla doğrulandı (Windows; Codex'te hook'lar onaylandıktan sonra); Gemini CLI ve Cursor test verileriyle sınandı: deneysel sayın. Bağlantı açıkken
ürün o aracın ayar dosyasına yalnızca kendi girdilerini ekler; sizin ve başka araçların girdileri korunur, kapatınca
yalnızca kendi girdileri geri alınır.

**Özetleyici seçimi:** `summary_provider` sabit bir araçsa ve `provider_fallback` kapalıysa yalnızca o denenir. Yedekleme
açıksa önce seçilen, sonra varsayılan sıra (Claude, Codex, Antigravity, Gemini, Cursor) denenir. Kurulu olmayan araç
atlanır; zaman aşımı, süreç hatası ya da geçici kota/ağ hatası sonraki adaya geçirir. `auto` modunda kimlik doğrulama
hatası ve boş yanıt da sonraki adaya geçirir. Kota, yanıt veren aracın hesabından düşer.

**Windows ve WSL:** varsayılan profil `windows-native` (kurulu `respected-brain.exe`). WSL içindeki bir kuruluma bağlanmak
için `setup --platform windows-wsl`: `wsl.exe` köprüsü kullanılır, yollar `/mnt/...` karşılığına çevrilir; WSL içinde
çalışan bir `respected-brain` ve aynı kasanın orada kaydı gerekir. Linux/macOS profili `posix`.

## 8. Yedekleme

Neyi yedeklemeli: **kasanın tamamı** (gizli dosyalar dahil) ve isterseniz **veri klasörü** (ayarlar, kasa kayıtları,
kişisel değişiklikler). Program klasörü yedek değildir; kurucuyla yeniden kurulur. İşlem yedekleri (`backups/`) yalnızca
o işlemde değişen dosyaları tutar, kasa yedeği yerine geçmez.

- **Elle:** yazan işlemler bittikten sonra kasayı arşivleyin, arşivi kasanın dışında tutun, başka bir yere açıp
  karşılaştırın. Aynı UUID'li iki kopyayı ayrı kasa olarak kaydetmeyin.
- **Restic (isteğe bağlı, `restic` kurulu olmalı):**

```text
respected-brain maintenance backup_restic --repo "<depo>" --password-file "<dosya>"            # önizleme
respected-brain maintenance backup_restic --repo "<depo>" --password-file "<dosya>" --apply    # yedekle ve doğrula
respected-brain maintenance backup_restic --repo "<depo>" --password-file "<dosya>" --restore-to "<yeni boş klasör>" [--snapshot <id>]
```

  Yedek, geri yüklenip her dosyanın SHA-256 değeri karşılaştırılarak doğrulanır. Geri yükleme yalnızca yeni ya da boş, kasa
  dışındaki bir klasöre yapılır; kasanın üzerine yazılmaz, gerekenleri siz kopyalarsınız. Gerçek restic 0.19.1 ile denendi.
- **Git anlık görüntüsü:** `respected-brain maintenance publish_git_snapshot` önizlemedir; `--apply` commit ve push yapar,
  yani veriyi dışarı gönderir. Yayından önce dosya adları ve içerik sır taramasından geçer; tanınmayan bir sır biçimi
  kaçabilir. Özel depo olması notlarda sır olmadığı anlamına gelmez.

## 9. Onarım ve kaldırma

```text
respected-brain repair      # program dosyalarını doğrular (bozuksa kurucuyu yeniden çalıştırmanızı söyler), kaydı ve bağlantıları yeniler
respected-brain recover     # yarım kalmış işlemleri geri alır; sonradan değiştirdiğiniz dosyayı zorla eski haline getirmez
```

Kaldırma yolları: Windows **Yüklü uygulamalar** → Respected Brain → Kaldır; kurucu → Kaldır; Hub → Brain →
Kaldır; sessiz `unins000.exe /VERYSILENT [/PURGE=1]`. Kaldırıcı "Ayarlar ve çalışma verileri de silinsin mi?" diye sorar
(varsayılan Hayır) ve ürünün `uninstall [--purge]` komutunu çalıştırır.

| Ne | Kaldırınca |
|---|---|
| Program (`app\`) | kaldırıcı siler |
| AI araçlarındaki kendi girdileri, zamanlanmış görev, kısayol | geri alınır; sizin ve başka araçların girdileri kalır |
| Sizin değiştirdiğiniz bir sahipli dosya | silinmez, çakışma olarak bildirilir |
| Kurulum kaydı | her zaman kalkar |
| Ayarlar ve çalışma verisi | kalır; "Evet" / `--purge` / `/PURGE=1` ile silinir |
| Not kasası | hiçbir durumda silinmez; aynı klasöre yeniden kurunca (`.respected.json` duruyorsa) kasa yeniden kaydedilir, notlara dokunulmaz |

## 10. Sorun giderme

| Belirti | Bakılacak yer |
|---|---|
| Kasa bulunamadı / UUID çakışması | `vault list`, kasadaki `.respected.json`, verdiğiniz `--vault`/`--vault-id`, `RESPECTED_VAULT_PATH` |
| Dolu klasöre kurulmuyor | Boş yeni bir klasör ya da Brain'in kullandığı bir kasa seçin |
| `daily` yazılmıyor | Aracın bağlantısı açık mı (`config`), hook etkin ve güvenilir mi, özetleyici aracın oturumu açık mı, `capture_mode` manual mı, veri klasöründeki `logs/` |
| Sabah özeti yok | `integrations.schedule`, `briefing_time`, işletim sisteminin görev zamanlayıcısı, aracın kotası |
| Arama eski sonuç veriyor | `respected-brain index-refresh` ya da `search --reindex` |
| MCP bozuk yanıt veriyor | AI aracının ayarındaki komut kurulu programı mı gösteriyor, `respected-brain health` |
| "Onarım gerekli" | Kurucuyu çalıştırıp **Onar / Güncelle** seçin |
| Yarım kalan işlem / geri alma çakışması | `respected-brain recover`; değişmiş dosyalar korunur, `backups/` ve `logs/` saklanır |

Kasa denetimi: `respected-brain maintenance vault_linter` (kırık bağlantı, yetim not) ve `tiling_check` (tekrar eden
notlar). Onarım, birleştirme ve içe alma araçları kasaya yazar ([COMMANDS.md](COMMANDS.md#bakım-araçları)). Pakette gelen `brain-doktor` becerisi AI aracınıza kasa
denetimi yaptırır.

Hata bildirirken işletim sistemi, `--version` çıktısı, kişisel bilgilerden arındırılmış komut, çıkış kodu ve hata kodunu
yazın. Ham döküm, sağlayıcı çıktısı, kimlik bilgisi ve ayar dosyasının tamamını herkese açık yere koymayın.
