# ⌨️ CLI Komut ve Seçenek Kataloğu

> Tablolar mevcut `cli._parser()` tanımlarından, komut çalıştırmadan üretildi. Kullanıcı rehberleri [belge merkezinde](../README.md). `<...>` örnekleri gerçek değerle değiştirilir. `respectedbrain` PATH yoksa tam native yol; kaynakta `python -m respectedbrain` kullanılır.

## 1. Çıkış kodları ve yan etkiler

Genel seçim/argüman hatası 2; Foundation/OS hatası 1; normal başarı 0. Setup/update/uninstall pending sonucu da 0 dönebilir: son receipt ayrıca doğrulanır. Search/maps/maintenance salt okunur kabul edilmez. Hook/MCP stdout protokoldür. `--help` ve `--version` kullanıcı kurulumu yapmaz.

## 2. Genel seçenekler

`respectedbrain --version`, `respectedbrain --help`; komut help örneği `respectedbrain setup --help`. Kasa selector destekleyen komutlarda --vault ile --vault-id birbirini dışlar. Configure/vault/recover/setup farklı seçim arayüzlerine sahiptir; her komuta aynı flag uygulanmaz.

### vault

Kasa kaydı/keşfi/listesi. register yazabilir; list/discover kurulum yapmaz.

#### vault register

| Argüman | Gereklilik / varsayılan | Değerler |
| --- | --- | --- |
| `path` | zorunlu | Path |
| `--new-identity` | isteğe bağlı; default: False | flag |

#### vault list

Ek argüman yoktur.

#### vault discover

| Argüman | Gereklilik / varsayılan | Değerler |
| --- | --- | --- |
| `path` | zorunlu | Path |

### configure

Ayar gösterir; --summary-provider varsa atomik config yazar.

| Argüman | Gereklilik / varsayılan | Değerler |
| --- | --- | --- |
| `--summary-provider` | isteğe bağlı | auto, codex, claude, antigravity, gemini, cursor |

### briefing

Zamanı gelmiş günlük derleme/brifing; model/not yazımı olabilir.

| Argüman | Gereklilik / varsayılan | Değerler |
| --- | --- | --- |
| `--vault` | isteğe bağlı | Path |
| `--vault-id` | isteğe bağlı | metin/argv |

### index-refresh

Arama dizinini (FTS ve açıksa anlamsal vektörler) artımlı günceller; kasayı değiştirmez, yalnız önbelleği yazar. Oturum başı/sonu ve günlük görev bunu kendiliğinden çalıştırır.

| Argüman | Gereklilik / varsayılan | Değerler |
| --- | --- | --- |
| `--vault` | isteğe bağlı | Path |
| `--vault-id` | isteğe bağlı | metin/argv |

### maps

Seçili kasanın haritalarını üretir; not yazar.

| Argüman | Gereklilik / varsayılan | Değerler |
| --- | --- | --- |
| `--vault` | isteğe bağlı | Path |
| `--vault-id` | isteğe bağlı | metin/argv |

### compile

Model ile knowledge derler; --dry-run önizleme.

| Argüman | Gereklilik / varsayılan | Değerler |
| --- | --- | --- |
| `--vault` | isteğe bağlı | Path |
| `--vault-id` | isteğe bağlı | metin/argv |
| `--trigger-claim` | isteğe bağlı | Path |
| `--before-date` | isteğe bağlı | YYYY-MM-DD |
| `--max-calls` | isteğe bağlı | int |
| `--dry-run` | isteğe bağlı; default: False | flag |

### flush

Transcript + session özetleyip daily yazar; gelişmiş hook işleri.

CLI, kendi state dizinindeki `hookin-*.json` girişini yalnız başarılı flush sonrası ve baytları değişmemişse temizler. Başarısız çağrının girdisini veya sonradan düzenlenen dosyayı silmez; önceden temizlenmiş bir girdi başarı sonucunu hataya dönüştürmez. Servisin yaşa bağlı stale-input temizliği ayrı yaşam döngüsü kuralıdır.

| Argüman | Gereklilik / varsayılan | Değerler |
| --- | --- | --- |
| `--vault` | isteğe bağlı | Path |
| `--vault-id` | isteğe bağlı | metin/argv |
| `--hook-input` | isteğe bağlı | Path |
| `--transcript` | isteğe bağlı | Path |
| `--session-id` | isteğe bağlı | metin/argv |
| `--reason` | isteğe bağlı; default: sessionend | metin/argv |
| `--maybe-compile` | isteğe bağlı; default: False | flag |

### open

Seçili kasa klasörünü dosya yöneticisinde açar (masaüstü kısayolu bunu çağırır). Yerel HTTP paneli kaldırıldı; not arama, hızlı yakalama ve brifing Hub'dadır. Eski `dashboard` adı (`--port/--open` yok sayılır) aynı işi yapar, böylece eski kısayollar çalışmaya devam eder.

| Argüman | Gereklilik / varsayılan | Değerler |
| --- | --- | --- |
| `--vault` | isteğe bağlı | Path |
| `--vault-id` | isteğe bağlı | metin/argv |

### search

FTS araması; teknik indeks/cache yazabilir.

| Argüman | Gereklilik / varsayılan | Değerler |
| --- | --- | --- |
| `--vault` | isteğe bağlı | Path |
| `--vault-id` | isteğe bağlı | metin/argv |
| `query` | isteğe bağlı; default: boş metin | metin/argv |
| `--reindex` | isteğe bağlı; default: False | flag |
| `--category` | isteğe bağlı | metin/argv |
| `--limit` | isteğe bağlı; default: 10 | int |
| `--json` | isteğe bağlı; default: False | flag |

### maintenance

İsimli bakım aracı; yan etkisi seçilen araca bağlı.

| Argüman | Gereklilik / varsayılan | Değerler |
| --- | --- | --- |
| `--vault` | isteğe bağlı | Path |
| `--vault-id` | isteğe bağlı | metin/argv |
| `name` | zorunlu | metin/argv |
| `argv` | isteğe bağlı | metin/argv |

### setup

Doğrulanmış native paketi kurar, boş kasa seed ve bağlantıları yönetir.

| Argüman | Gereklilik / varsayılan | Değerler |
| --- | --- | --- |
| `--vault` | isteğe bağlı | Path |
| `--package` | isteğe bağlı | Path |
| `--user-name` | isteğe bağlı | metin/argv |
| `--user-bio` | isteğe bağlı | metin/argv |
| `--companion` | isteğe bağlı | metin/argv |
| `--os-name` | isteğe bağlı | metin/argv |
| `--summary-provider` | isteğe bağlı | auto, codex, claude, antigravity, gemini, cursor |
| `--platform` | isteğe bağlı | windows-native, posix, windows-wsl |
| `--global, --no-global` | isteğe bağlı | flag |
| `--mcp, --no-mcp` | isteğe bağlı | flag |
| `--schedule, --no-schedule` | isteğe bağlı | flag |
| `--shortcut, --no-shortcut` | isteğe bağlı | flag |
| `--clients` | isteğe bağlı; `--global` için AI istemcileri (virgülle: claude,codex,gemini,antigravity,cursor,windsurf,claude-desktop,vscode-agents); default: hepsi | metin |
| `--mcp-clients` | isteğe bağlı; `--mcp` için AI istemcileri; default: `--clients` | metin |

### update

Yeni doğrulanmış paketten günceller; Windows pending olabilir.

| Argüman | Gereklilik / varsayılan | Değerler |
| --- | --- | --- |
| `--vault` | isteğe bağlı | Path |
| `--vault-id` | isteğe bağlı | metin/argv |
| `--package` | zorunlu | Path |

### repair

Sahipli program/desired bağlantıları onarır.

| Argüman | Gereklilik / varsayılan | Değerler |
| --- | --- | --- |
| `--vault` | isteğe bağlı | Path |
| `--vault-id` | isteğe bağlı | metin/argv |

### uninstall

Sahipli program/bağlantıları kaldırır; not kasasını hedeflemez.

| Argüman | Gereklilik / varsayılan | Değerler |
| --- | --- | --- |
| `--vault` | isteğe bağlı | Path |
| `--vault-id` | isteğe bağlı | metin/argv |
| `--purge-data` | isteğe bağlı; default: False | flag |

## 4. İç OS protokol komutları

Alt çizgiyle başlayan `_resume-operation` komutu hash doğrulanmış ertelenmiş işlem protokolüdür. Kullanıcı bakım komutu gibi elle çağrılmaz; request/proof doğrulama sözleşmesini atlamak için kullanılamaz. Kesin arayüz `cli.py` ve `deferred.py` içindedir.
