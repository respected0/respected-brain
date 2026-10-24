# Brain: ne yaparsan nerede ne oluşur

Bu belge, Brain'i kurduğunda, ayarlarını değiştirdiğinde, kullandığında ve kaldırdığında **bilgisayarında hangi dosyanın
nerede, hangi şartla ve neden oluştuğunu** anlatır. Kod okunarak ve boş bir kullanıcı klasöründe gerçek kurucu çalıştırılarak
doğrulandı (2026-10-24, `0.1.0-beta.1`). Genel kullanım için [USAGE.md](USAGE.md), iç yapı için [ARCHITECTURE.md](ARCHITECTURE.md).

## 1. Tek bakışta

| Ne | Nerede | Kim oluşturur | Ne zaman |
|---|---|---|---|
| Program (`respected-brain.exe`, kaldırıcı) | `%LOCALAPPDATA%\Respected\RespectedBrain\app` | Kurucu | Her kurulumda |
| Windows "Yüklü uygulamalar" kaydı | `HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\{2F6A9C41-85D7-4B3E-9A10-C7E4D58B1F23}_is1` | Kurucu | Her kurulumda |
| Ayarlar, kurulum kaydı, günlükler, yedekler | `%LOCALAPPDATA%\Respected\RespectedBrain\data` | Brain (`setup`) | Her kurulumda |
| Not kasası | Kurulumda seçtiğin klasör (varsayılan `Belgeler\RespectedOS`) | Brain (`setup`) | Her kurulumda, klasör yoksa ya da boşsa |
| AI araçlarının ayar dosyaları | Her aracın kendi klasörü (bölüm 3 ve 4) | Brain | Yalnızca ilgili anahtarı açtıysan **ve** araç bilgisayarında kuruluysa |
| Zamanlanmış görev | Windows Görev Zamanlayıcı | Brain | Yalnızca "Sabah özeti görevi" açıksa |
| Masaüstü kısayolu | `Masaüstü\Obsidian - <kasa adı>.url` | Brain | Yalnızca "Masaüstü kısayolu" açıksa |
| Başlat menüsü kaydı | yok | | Brain bir pencere uygulaması değildir; arayüzü Hub'dır |

Kurucuda dört anahtarın **hepsi varsayılan olarak kapalıdır**: "Oturumları hafızaya yakala", "Hafıza MCP sunucusu", "Sabah
özeti görevi", "Masaüstü kısayolu". Hiçbirini açmazsan kurulum yalnızca ilk beş satırı oluşturur; AI araçlarına, Görev
Zamanlayıcı'ya ve masaüstüne dokunmaz.

## 2. Kurulum: adım adım

1. **Kurucu** programı `app` klasörüne açar ve "Yüklü uygulamalar" kaydını yazar. Yönetici izni istemez; her şey senin
   kullanıcın altındadır. `%TEMP%` içine kısa süreli `is-XXXX.tmp` klasörü açar (kendi dosyalarını çıkarır), bitince siler.
2. **Kurucu `respected-brain setup` komutunu çalıştırır.** Brain:
   - `data` klasörünü ve `config.json` (ayarlar, kasa kaydı) ile `install-manifest.json` (hangi dosyanın kime ait olduğu) dosyalarını yazar.
   - Kasa klasörünü şablondan oluşturur (bölüm 5). Klasör **boşsa ya da yoksa** oluşturur. İçinde senin notların varsa
     kurucu bunu **kasa sayfasında baştan** reddeder ("Boş ya da yeni bir klasör seç"); sessiz kurulumda hiçbir şey
     kurmadan hata koduyla (7) durur. Daha önce Brain'in kasası olmuş bir klasörse (içinde `.respected.json`
     varsa) yeniden kaydeder, notlarına dokunmaz.
   - Seçtiğin bağlantıları bölüm 3-4'teki kurallarla yazar.
3. Herhangi bir adım hata verirse Brain kendi yaptığı değişiklikleri geri alır, kurucu program klasörünü ve "Yüklü
   uygulamalar" kaydını da siler (geriye hiçbir şey kalmaz) ve son sayfada "Kurulum tamamlanamadı" der. Kurucuyu yeniden
   çalıştırabilirsin. Sessiz kurulumda **kasa klasörü hatası** 7 koduyla, **ürünün `setup` komutunun hatası** ise 0 koduyla
   biter (Inno Setup kurulum sonrası adımda kod veremiyor); Hub sonucu ayrıca doğrular ve "ürünün kaydı bulunamadı" der.

**Hub'dan kurulum aynı şeydir:** Hub, Brain'in kendi kurucusunu sessiz modda çalıştırır (`/VAULT=` ve `/SET=anahtar=değer`
anahtarlarıyla). Sonuç, kurucuyu elle çalıştırmakla aynıdır.

## 3. "Oturumları hafızaya yakala" (hook'lar ve kurallar)

Bu anahtar açıksa Brain, **Kaynaklar** listesinde işaretlediğin araçlara üç şey ekler: oturum olaylarını yakalayan **hook**,
asistana kasanın yerini söyleyen **kural metni** ve Brain'in **becerileri** (`brain-doktor`, `inbox-duzenle` gibi 9 beceri).

**Şart:** araç bilgisayarında **kurulu** olmalı. Brain bunu aracın ayar klasörünün var olmasıyla anlar (tablo 3.2). Kurulu
olmayan bir araç işaretlenmiş olsa bile **hiçbir şey yazılmaz ve klasörü oluşturulmaz**. Araç sonradan kurulursa
Hub'da ayarları yeniden kaydet ya da "Onar" de; o zaman yazılır.

### 3.1 Her araçta nasıl çalışıyor

| Araç | Hook nasıl bağlanır | Kural metni | Beceriler | Senin onayın |
|---|---|---|---|---|
| **Claude Code** | Yerel **eklenti** (`respected-brain`): `SessionStart`, `UserPromptSubmit`, `Stop`, `SessionEnd`, `PreCompact` hook'ları eklentinin içindedir | `~\.claude\CLAUDE.md` içinde işaretli blok | Eklentinin içinde | Claude'da eklentiye izin vermen gerekir |
| **Codex** | Yerel **eklenti** + `notify` köprüsü. Mevcut `notify` ayarın varsa **silinmez**, Brain'in köprüsü onu zincirler | `~\.codex\AGENTS.md` içinde işaretli blok | Eklentinin içinde | Codex'te `/hooks` ile hook'ları onaylaman gerekir; içerik değişince onay yeniden istenir |
| **Gemini CLI** | `~\.gemini\settings.json` içine hook'lar: `SessionStart`, `BeforeAgent`, `AfterAgent`, `SessionEnd`, `PreCompress` | `~\.gemini\GEMINI.md` içinde işaretli blok | `~\.gemini\skills\<ad>\SKILL.md` | Yok |
| **Antigravity** | `~\.gemini\config\hooks.json` içinde `respected-brain` anahtarı: `PreInvocation`, `Stop` | `~\.gemini\GEMINI.md` (Gemini CLI ile **aynı dosya**, tek blok) | `~\.gemini\config\skills\<ad>\SKILL.md` | Yok |
| **Cursor** | `~\.cursor\hooks.json` içine `sessionStart`, `beforeSubmitPrompt`, `sessionEnd`, `preCompact`, `afterAgentResponse` | `~\.cursor\rules\respected-brain.mdc` | `~\.cursor\skills\<ad>\SKILL.md` | Yok |

Neden farklı? **Araçların kendi sistemi öyle.** Claude ve Codex eklenti sistemi sunar: hook'lar ve beceriler tek pakette
Brain'in veri klasöründe durur, araca yalnızca "bu eklentiyi kullan" kaydı yazılır. Gemini CLI, Antigravity ve Cursor'da eklenti
sistemi yoktur; hook'ları ve becerileri doğrudan kendi klasörlerine yazmak zorundayız. Hepsi **global** (kullanıcı klasöründe)
yazılır; kasanın içinde hiçbir araç klasörü oluşmaz.

Claude ve Codex için Brain, ayrıca varsa `claude plugin marketplace add`, `claude plugin install` ve `codex plugin add` komutlarını
çalıştırır. Komut PATH'te yoksa atlanır; kurulumu bozmaz, "Onar" sonradan yeniden dener.

### 3.2 Aracın "kurulu" sayılması (Hub'daki "Bu bilgisayarda bulundu")

| Araç | Kurulu sayılma şartı |
|---|---|
| Claude Code | `~\.claude` klasörü ya da `~\.claude.json` dosyası var |
| Codex | `~\.codex` klasörü var |
| Gemini CLI ve Antigravity | `~\.gemini` klasörü var (ikisi için ortak) |
| Cursor | `~\.cursor` klasörü var |
| Windsurf | `~\.codeium` klasörü var |
| Claude Desktop | `%APPDATA%\Claude` klasörü var |
| Cline / Roo (VS Code) | `%APPDATA%\Code\User\globalStorage\saoudrizwan.claude-dev` ya da `rooveterinaryinc.roo-cline` klasörü var |

Brain bu klasörleri **kendisi oluşturmaz**; araç ilk çalıştığında kendi klasörünü açar.

### 3.3 Ne zaman değişir

- Anahtarı kapatırsan ya da aracı listeden çıkarırsan Brain **yalnızca kendi eklediği** blok ve girdileri geri alır. Senin
  ayarların, başka araçların hook'ları ve metinlerin kalır.
- Bir dosyayı sen elle değiştirdiysen Brain onu "senin" sayar ve üzerine yazmaz; çakışmayı bildirir.

## 4. "Hafıza MCP sunucusu"

Açıksa seçtiğin araçlara, kasada aramak ve not okumak için **MCP kaydı** eklenir. Kayıt, aracın ayar dosyasında
`respected-brain` adlı bir sunucudur ve `respected-brain.exe mcp --vault-id <UUID>` komutunu çalıştırır. Sunucuyu araç
gerektiğinde kendi başlatır (stdio); arka planda sürekli çalışan bir şey yoktur. Aynı şart: araç bilgisayarında kurulu olmalı.

| Araç | MCP kaydı nerede | Notlar |
|---|---|---|
| Claude Code | `~\.claude.json` içinde `mcpServers.respected-brain` | Dosya yoksa bu kayıtla birlikte oluşur (araç kuruluysa) |
| Claude Desktop | `%APPDATA%\Claude\claude_desktop_config.json` | Yalnızca MCP, hook yok |
| Antigravity | `~\.gemini\config\mcp_config.json` **ve** `~\.gemini\antigravity-ide\mcp\respected-brain\` (`instructions.md` ile 5 araç şeması `.json`) | Antigravity iki yerden okur |
| Cursor | `~\.cursor\mcp.json` | |
| Windsurf | `~\.codeium\windsurf\mcp_config.json` | Yalnızca MCP, hook yok |
| Cline / Roo | VS Code `globalStorage` altındaki `cline_mcp_settings.json` / `roo_mcp_settings.json` | Eklenti klasörü varsa |
| Codex, Gemini CLI | **yazılmaz** | Brain bu ikisine MCP kaydı eklemez; hook ve eklenti yolunu kullanır |

`mcp_write` ayarı kapalıyken (varsayılan) araçlar kasadan yalnızca **okur**. Açarsan yalnızca
`🔮 850-Companion\Inbox\MCP` içine geri alınabilir not yazabilirler.

## 5. Kasa klasöründe ne oluşur

Kurulumda şablondan şunlar gelir:

```text
<kasa>/
  .respected.json            kasanın kalıcı kimliği (UUID); silme
  .obsidian/                 Obsidian ayarları
  daily/                     oturum özetleri (günlük dosyalar)
  knowledge/                 derlenmiş bilgi: index.md, concepts/, connections/, log.md
  🎯 100-Command-Center/     Dashboard, Vault-Map, Skills-Map, Briefings/
  🔮 850-Companion/          Core, Kurallar, Threads, Last-Session, Journal, events/
  📥 000-Inbox/Dump/  🏰 300-Projects/  🧠 500-Knowledge/  🛠️ 600-Arsenal/  📋 Templates/  📦 900-Archive/
```

Brain **kendi dosyalarını** (günlüğün programa ait blokları, `knowledge/`, brifingler, `Last-Session.md`) yazar; senin yazdığın
notlara ve `Core.md`/`Kurallar.md` gibi düzenlediğin dosyalara üzerine yazmaz. Kaldırınca **kasa hiçbir durumda silinmez**.

## 6. Kullanırken (çalışma anında) ne oluşur

| Olay | Ne oluşur | Nerede |
|---|---|---|
| AI aracında oturum başlar | Hook Brain'i çağırır, Brain araca bağlamı verir; yazma yapmaz | |
| Her mesaj / tur | Olay kaydı (ham, kısa) | `🔮 850-Companion\events\` (eskiler `events\archive\`) |
| Oturum biter (hafıza yakalama **Otomatik** ise) | Döküm, gizli bilgiler maskelendikten sonra **senin seçtiğin AI aracına** özetletilir; özet günlüğe yazılır | `daily\YYYY-MM-DD.md`, `🔮 850-Companion\Last-Session.md`; durum `data\vaults\<UUID>\state` |
| Önceki günler derlenir | Bilgi notları ve dizin | `knowledge\` |
| Sabah özeti (görev açıksa 08:00 ya da seçtiğin saat) | Brifing | `🎯 100-Command-Center\Briefings\YYYY-MM-DD.md` |
| Arama | Tam metin dizini (yeniden üretilebilir) | `data\vaults\<UUID>\cache` |
| Anlamsal arama açılırsa | Bir kez ~460 MB model ve çalışma ortamı indirilir | `data\semantic-runtime` |
| `archive_transcripts` açıksa (varsayılan kapalı) | Gizli bilgisi ayıklanmış döküm kopyası | kasanın **dışında** |
| Her işlem | Günlük ve yedek | `data\logs`, `data\backups`, `data\receipts` |

Hafıza yakalamayı **Elle** yaparsan hiçbir oturum kendiliğinden işlenmez; Hub'dan "Şimdi yakala" dediğinde çalışır.

**Geçici dosyalar (`%TEMP%` ve yanlarında):** Brain, bir dosyayı güvenli yazmak için hedefin yanına `.<ad>.tmp` açıp yer
değiştirir (işlem bitince kalmaz). Dahili kaynakları açarken `%TEMP%` altında `respected-resource-*` klasörü kullanır ve siler.
`Local\Temp` klasörünü Windows oluşturur; Brain ve kurucu orada yalnızca bu kısa ömürlü dosyaları tutar.

## 7. Zamanlanmış görev ve masaüstü kısayolu

- **Sabah özeti görevi:** Görev Zamanlayıcı'da `respected-morning-briefing-<kasa UUID>` adlı günlük görev. Her gün `briefing_time`
  saatinde (varsayılan 08:00) `respected-brain.exe briefing` çalıştırır; bilgisayar o saatte kapalıysa açılınca çalışır; en çok
  30 dakika. Anahtarı kapatınca ya da Brain'i kaldırınca silinir.
- **Masaüstü kısayolu:** `Masaüstü\Obsidian - <kasa adı>.url`, `obsidian://open?vault=<kasa adı>` açar. Obsidian kurulu değilse
  ya da kasayı hiç açmadıysa **kısayol yine yazılır** ama çalışmaz; kurulum bunu uyarı olarak söyler.

## 8. Güncelleme ve onarım

- **Onar / Güncelle** (kurucuyu yeniden çalıştırmak): programı yenisiyle değiştirir; eski sürümün dosyaları silinir.
- Güncellemeden önce kurucu eski programı ve veri dosyalarını `%LOCALAPPDATA%\Respected\RespectedBrain\update-backup`
  klasörüne yedekler; bir şey ters giderse geri yükler ve işlem tamamlanınca yedeği siler.
- `repair` komutu bağlantıları (hook, kural, MCP, görev) bugünkü ayarlarına göre yeniden yazar; sonradan kurduğun araç da bu
  sırada bağlanır.

## 9. Kaldırma

| Ne | Sonuç |
|---|---|
| Program klasörü, "Yüklü uygulamalar" kaydı, kurulum kaydı | **Silinir** |
| AI araçlarındaki Brain girdileri (hook, kural bloğu, MCP kaydı, eklenti, beceriler) | **Geri alınır**; yalnızca Brain'in eklediği kısım |
| Zamanlanmış görev ve masaüstü kısayolu | **Silinir** |
| Ayarlar ve çalışma verisi (`data`) | **Kalır**; "çalışma verileri de silinsin" ya da `uninstall --purge` ile silinir |
| **Not kasası** | **Hiçbir durumda silinmez** |

Aynı kasaya sonradan yeniden kurarsan Brain onu tanır (`.respected.json`) ve notlarına dokunmadan yeniden bağlar.

## 10. Sık sorulanlar

**`.claude.json`, `.claude`, `.codex`, `.gemini` bizden mi oluşuyor?** Yalnızca o araç kuruluyken ve ilgili anahtarı açtıysan
**içlerine** yazarız. Kurulu olmayan araç için klasörünü **oluşturmayız**. Bu dosya ve klasörleri aracın kendisi de oluşturur;
Brain onlara yalnızca kendi bloğunu ekler.

**Kurulum bitti ama hiçbir şey çalışmıyor.** Claude'da eklentiye, Codex'te hook'lara onay vermen gerekir ve aracı yeniden
başlatman gerekir. Onay olmadan hafıza yazılmaz.

**Hub'da "Eklenir" yazan değişiklikler görüyorum.** Hub, ayarladığın ile makinedekini karşılaştırır. Bir araç sonradan
kurulduysa o aracın girdileri "Eklenir" görünür; uygulayınca yazılır ve liste boşalır.

**Ne gönderiliyor?** Bkz. [PRIVACY.md](../PRIVACY.md): özetleme için dökümler yalnızca senin seçtiğin AI aracının sağlayıcısına gider.
