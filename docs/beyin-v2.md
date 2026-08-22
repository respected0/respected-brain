# beyin.md v2: Build Me a Second Brain That Remembers On Its Own

> You are Claude Code. The human in front of you wants their own AI-native "second brain" running
> on Obsidian + Claude Code, with memory that survives across sessions **and writes itself**.
> This file is your complete, self-contained build spec. Read it once, top to bottom, then execute
> it phase by phase. You need no other context.
>
> Source: https://avenox.lol/beyin.md · Repo: https://github.com/avenoxai/avenoxbeyin

---

## The idea (say this to the user, in their own words)

Most people use an AI chat and it forgets them every session. A second brain fixes that: a local
Obsidian vault for everything they know and do, driven by Claude Code, with a memory layer that
survives across sessions. v1 of this system did that already, but it leaned on the model
remembering to write its own memory files at the end of a session. Whenever it forgot, that day was
gone.

v2's thesis: **memory must be a mechanism, not a discipline.** Session end and pre-compaction are
caught by hooks, a small background call summarizes the conversation into a daily log, and once a
day a compiler turns those logs into linked articles in a knowledge base. The next morning that
knowledge base is already in context. Nobody has to remember anything.

There is no video to watch and no tutorial to follow. This file is the tutorial, and you are the
one executing it.

---

## Rules for you, Claude (read before doing anything)

1. **Speak Turkish to the user by default.** The audience is Turkish. Match the language they
   write in, but default to warm, direct Turkish. This file is English only so your instructions
   stay precise; the system you build talks to them in Turkish.
2. **Interview first, build second.** Do the interview before touching the filesystem.
3. **Never destroy.** If a target file or folder exists, show it and ask. Default to merge or skip,
   never a silent clobber. If the user already has a brain, their memory files are read-only for
   you.
4. **Resolve every `{{PLACEHOLDER}}`** before writing files. Never leave a literal `{{...}}`
   anywhere.
5. **Don't block on optional steps.** obsidian-cli, mem0, the swift icon. If an install fails, log
   it, tell the user, continue.
6. **Verify each phase** with a quick check before moving on. End with the first-run report.
7. **Be the demo.** This is often filmed. Narrate what you are doing in short Turkish lines as you
   go: "Vault iskeletini kuruyorum...", "Hafıza motorunu bağlıyorum...", "Gece derleyicisini
   yerine koyuyorum...". Short sentences, no walls of text.
8. **Zero cost, zero keys.** Nothing here needs an API key. The background summarizer and the
   compiler run on the subscription the user already pays for, through `claude -p`.

Placeholders you must resolve:
`{{OS_NAME}}` · `{{USER_NAME}}` · `{{USER_BIO}}` · `{{COMPANION}}` · `{{VAULT_PATH}}` ·
`{{SCOPE}}` · `{{USE_MEM0}}` · `{{TODAY}}` (YYYY-MM-DD)

| Placeholder | Nereden gelir | Örnek |
| --- | --- | --- |
| `{{OS_NAME}}` | makine adından türetilir, kullanıcı onaylar | `AylinOS` |
| `{{USER_NAME}}` | soru 1 | `Aylin` |
| `{{USER_BIO}}` | soru 2 | `Ürün tasarımcısı, yan projeler yürütüyor` |
| `{{COMPANION}}` | soru 3 | `Echo` |
| `{{VAULT_PATH}}` | 0.3 | `~/Documents/AylinOS` |
| `{{SCOPE}}` | soru 4 | `core+goals` |
| `{{USE_MEM0}}` | soru 5 | `evet` |
| `{{TODAY}}` | `date +%F` | `2026-08-22` |

---

## STEP 0: Mevcut beyin var mı? (ask this before anything else)

Ask the user in Turkish: **"Daha önce kurulmuş bir beynin var mı? Varsa klasör yolunu ver."**
Then scan the two default locations anyway:

```bash
for D in "$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents"/* "$HOME/Documents"/*; do
  [ -d "$D" ] || continue
  if [ -f "$D/CLAUDE.md" ] && ls -d "$D/🔮 850-"* >/dev/null 2>&1; then
    echo "ADAY: $D  sürüm: $(cat "$D/.beyin-version" 2>/dev/null || echo 'v1')"
  fi
done
```

| Bulgu | Yol |
| --- | --- |
| Aday yok | Yeni kurulum. FAST PATH, sonra gerekirse from-scratch fallback |
| Aday var, `.beyin-version` yok | **Yükseltme.** FAST PATH ile repoyu klonla, `SETUP.md` MODE B |
| Aday var, sürüm `2.0.0` | Zaten v2. Vault'ta `claude` açıp `beyin doktor` çalıştır, bitir |

The upgrade path is not optional politeness, it is the only correct move: a v1 vault holds months
of the user's memory. Never build a fresh vault next to one that already exists without saying so
out loud and getting a yes.

---

## FAST PATH: clone the open-source template (recommended, covers both cases)

```bash
git clone https://github.com/avenoxai/avenoxbeyin.git /tmp/avenoxbeyin && cd /tmp/avenoxbeyin
```

Then read and follow `SETUP.md` in that repo. It decides the mode (fresh install or upgrade from
v1) and carries the full interview, personalize, upgrade, launcher and verification runbook. The
scaffold is already in `template/`, so you only copy and fill in the blanks.

If the clone fails (no network, no git), fall back to the phases below. They produce the same
system, with one honest limitation spelled out in PHASE 4.

---

## PHASE 0: Discover and interview (from-scratch fallback)

### 0.1 Detect the machine name, derive the OS name

```bash
scutil --get ComputerName 2>/dev/null || hostname
```

PascalCase it and append `OS`. Strip "MacBook", "Pro", "Air", "iMac", "'s", apostrophes, dashes.
`Johns-MacBook-Pro` → `JohnOS`, `aylin's Mac` → `AylinOS`, `DESKTOP-AB12` → `Ab12OS`.
Propose `{{OS_NAME}}`, let the user override.

### 0.2 Ask exactly these questions (Turkish, conversational, not a form)

1. **İsmin ne?** → `{{USER_NAME}}`
2. **Ne iş yapıyorsun, bu beyni en çok ne için kullanacaksın?** (1 veya 2 cümle) → `{{USER_BIO}}`
3. **AI ortağına ne isim vermek istersin?** (Avenox'unki "Echo") → `{{COMPANION}}`
4. **Kapsam, neye ihtiyacın var?** → `{{SCOPE}}`
   - `core` (herkes): Inbox, Knowledge, Projects, Command-Center, ortağın hafızası, kancalar,
     `daily/`, `knowledge/`
   - `+goals` ⚔️ 200-Goals · `+money` 🔐 400-Vault · `+body` 💪 700-Body · `+mind` 🧘 800-Mind
   - `full`: hepsi
5. **Semantik hafıza (mem0) ekleyelim mi?** Açıkla: dosya tabanlı hafıza API'siz çalışır ve
   herkese yeter. mem0 üstüne anlamsal arama katmanı koyar, **temel sürümü tamamen ücretsiz**
   (mem0.ai'den ücretsiz API key, kredi kartı yok). Önerilir. → `{{USE_MEM0}}` (varsayılan: evet)

### 0.3 Pick the vault location → `{{VAULT_PATH}}`

- If `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/` exists (Obsidian + iCloud), default
  to `.../Documents/{{OS_NAME}}` so it syncs across devices.
- Else default to `~/Documents/{{OS_NAME}}`.
- Always confirm the path before creating anything.

Set `{{TODAY}}` from `date +%F`.

---

## PHASE 1: Prerequisites

Check each, install only what is missing, narrate progress.

```bash
# Homebrew, required on macOS
command -v brew >/dev/null || /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Obsidian, required
ls "/Applications/Obsidian.app" >/dev/null 2>&1 || brew install --cask obsidian

# Obsidian CLI, OPTIONAL, never block
command -v obsidian >/dev/null 2>&1 || (brew tap yakitrak/yakitrak 2>/dev/null && brew install yakitrak/yakitrak/obsidian-cli 2>/dev/null) || echo "obsidian-cli atlandı (opsiyonel)"

# python3, required for the v2 machine layer
command -v python3 >/dev/null && python3 -V || echo "PYTHON3 YOK: xcode-select --install"
```

Claude Code is already installed, the user is running you. Do not reinstall it. If `python3` is
missing and cannot be installed, say so plainly in Turkish: the vault and the hooks still work, the
automatic daily log and knowledge compilation stay off until python3 exists.

---

## PHASE 2: Create the vault skeleton

```
{{OS_NAME}}/
├── 📥 000-Inbox/Dump/          # ham yakalama
├── 🎯 100-Command-Center/      # Dashboard
├── 🏰 300-Projects/
├── 🧠 500-Knowledge/           # insanın yazdığı notlar
├── 🛠️ 600-Arsenal/
├── 🔮 850-Companion/           # ortağın kalıcı hafızası
├── daily/                      # makine yazar: günlük loglar
├── knowledge/
│   ├── concepts/
│   └── connections/
├── 📦 900-Archive/
└── 📋 Templates/
```

Scope add-ons only if selected: `⚔️ 200-Goals`, `🔐 400-Vault`, `💪 700-Body`, `🧘 800-Mind`.

**The memory folder name is fixed: `🔮 850-Companion`.** The hooks and the scripts read that exact
path. `{{COMPANION}}` is the persona's name and lives inside the files, not in the folder name.
Tell the user this once so it does not look like a bug.

Control plane inside the vault:

```
{{OS_NAME}}/.claude/
├── hooks/.state/
├── scripts/.state/
├── skills/
└── settings.json
```

And a `.gitignore` at the vault root:

```
.claude/settings.local.json
.claude/hooks/.state/
.claude/scripts/.state/*
!.claude/scripts/.state/.gitkeep
.DS_Store
.obsidian/workspace*
.obsidian/cache
```

Write `.beyin-version` at the vault root containing exactly `2.0.0`.

---

## PHASE 3: Write `{{OS_NAME}}/CLAUDE.md` (the router)

Keep it short, under 40 lines. It is a router, not an encyclopedia. Resolve all placeholders.

```markdown
# {{OS_NAME}}: {{USER_NAME}}'in ikinci beyni

Sen {{COMPANION}}'sun, {{USER_NAME}}'in düşünme ortağı. Genel amaçlı bir asistan değil, hatırlayan
ve devamlılık kuran bir ekip arkadaşısın. Türkçe konuşursun, doğrudan ve sıcak, dolgu cümlesi yok.
{{USER_NAME}} hakkında: {{USER_BIO}}

## Yükleme sırası
1. `🔮 850-Companion/Core.md` (kim olduğun)
2. Son oturum ve aktif threadler (kanca otomatik enjekte eder)
3. `🔮 850-Companion/Kurallar.md` (kanca otomatik enjekte eder)
4. `knowledge/index.md` (bilgi tabanı indeksi, kanca enjekte eder)

## Göreve göre yönlendirme
| Görev | Yer |
| --- | --- |
| Hızlı yakalama | `📥 000-Inbox/Dump/` |
| Proje işi | `🏰 300-Projects/<proje>/` |
| Kalıcı bilgi (insan eliyle) | `🧠 500-Knowledge/` |
| Derlenmiş bilgi (makine) | `knowledge/` (elle düzenleme, derleyici yönetir) |
| Günlük log (makine) | `daily/` |
| Genel bakış | `🎯 100-Command-Center/Dashboard.md` |

## Hafıza protokolü
Makine `daily/` ve `knowledge/` klasörlerini kendi yazar. Sen ilişki katmanını yazarsın: anlamlı
her oturumun sonunda `🔮 850-Companion/Last-Session.md` üzerine yaz, `Threads.md` içindeki açık
hatları güncelle, önemli bir şey olduysa `Journal.md` içine kısa bir giriş ekle.
{{USER_NAME}} seni düzelttiğinde ("bunu böyle yapma") bunu `Kurallar.md` içine kural olarak ekle.

## Devir kuralı
Her anlamlı oturum iz bırakır: ya bir not, ya bir karar, ya güncellenmiş bir dosya.

## Doğrulama
Bu dosya bir yönlendiricidir. Projenin gerçeği için güncel dosyaları oku, buradan varsayma.
```

---

## PHASE 4: The engine: hooks and scripts

v2's engine is four bash hooks plus two python scripts. The scripts are too long to inline here
without drift, so fetch them from the repo. Try this first:

```bash
V="{{VAULT_PATH}}"
RAW="https://raw.githubusercontent.com/avenoxai/avenoxbeyin/main/template/.claude"
mkdir -p "$V/.claude/hooks/.state" "$V/.claude/scripts/.state" "$V/.claude/skills"
OK=1
for F in hooks/lib.sh hooks/session-start.sh hooks/prompt-counter.sh hooks/session-end.sh \
         hooks/pre-compact.sh scripts/flush.py scripts/compile.py settings.json; do
  curl -fsSL "$RAW/$F" -o "$V/.claude/$F" || OK=0
done
chmod +x "$V/.claude/hooks/"*.sh
if [ "$OK" = "1" ]; then
  for H in "$V/.claude/hooks/"*.sh; do bash -n "$H" || OK=0; done
  python3 -m py_compile "$V/.claude/scripts/"*.py || OK=0
fi
echo "motor: $OK"
```

Also fetch the two skills, they are what makes the system diagnosable and importable:

```bash
SK="https://raw.githubusercontent.com/avenoxai/avenoxbeyin/main/template/.claude/skills"
mkdir -p "$V/.claude/skills/beyin-doktor" "$V/.claude/skills/gecmis-import"
curl -fsSL "$SK/beyin-doktor/SKILL.md"  -o "$V/.claude/skills/beyin-doktor/SKILL.md"
curl -fsSL "$SK/gecmis-import/SKILL.md" -o "$V/.claude/skills/gecmis-import/SKILL.md"
```

### If there is no network at all: degraded mode (v1 hooks only)

Write these three hooks by hand and tell the user, in Turkish and without softening it, that this
is the **degraded v1 mode**: continuity works, the automatic daily log and the knowledge
compilation do not, and they can upgrade any time by cloning the repo and following `SETUP.md`.

`.claude/hooks/session-start.sh`:

```bash
#!/bin/bash
# Session Start: inject continuity (last session + threads + identity)
VAULT_DIR="$(dirname "$(dirname "$(dirname "$0")")")"
MEM_DIR="$VAULT_DIR/🔮 850-Companion"
STATE_DIR="$VAULT_DIR/.claude/hooks/.state"
mkdir -p "$STATE_DIR"
date +%s > "$STATE_DIR/session_start_time"
echo "0" > "$STATE_DIR/prompt_count"

LAST_SESSION=""
[ -f "$MEM_DIR/Last-Session.md" ] && LAST_SESSION=$(sed -n '/^## Session:/,/^## Previous/p' "$MEM_DIR/Last-Session.md" 2>/dev/null | head -50 | sed '$d')

THREADS=""
[ -f "$MEM_DIR/Threads.md" ] && THREADS=$(sed -n '/^## Active/,/^## Closed/p' "$MEM_DIR/Threads.md" 2>/dev/null | grep -E "^### |^\*\*Status:\*\*" | head -12)

KURALLAR=""
[ -f "$MEM_DIR/Kurallar.md" ] && KURALLAR=$(head -60 "$MEM_DIR/Kurallar.md" 2>/dev/null)

REFLECTION=""
if [ -f "$STATE_DIR/needs_reflection" ]; then
  REFLECTION="Önceki oturum hafıza güncellemeden bitti: $(cat "$STATE_DIR/needs_reflection"). Anlamlı bir şey olduysa 🔮 850-Companion dosyalarını güncelle."
  rm -f "$STATE_DIR/needs_reflection"
fi

CTX=""
[ -n "$REFLECTION" ] && CTX="${CTX}${REFLECTION}\n\n"
[ -n "$LAST_SESSION" ] && CTX="${CTX}[Hafıza: Son Oturum]\n${LAST_SESSION}\n\n"
[ -n "$THREADS" ] && CTX="${CTX}[Hafıza: Aktif Threadler]\n${THREADS}\n\n"
[ -n "$KURALLAR" ] && CTX="${CTX}[Hafıza: Kurallar]\n${KURALLAR}\n\n"
CTX="${CTX}[Hafıza] Kimlik: {{COMPANION}}, {{USER_NAME}}'in düşünme ortağı. Hafıza protokolü zorunludur."

if [ -n "$CTX" ]; then
  ESC=$(printf '%s' "$CTX" | python3 -c "import sys,json; print(json.dumps(sys.stdin.read()))" 2>/dev/null)
  [ -n "$ESC" ] && echo "{\"hookSpecificOutput\":{\"hookEventName\":\"SessionStart\",\"additionalContext\":${ESC}}}"
fi
exit 0
```

`.claude/hooks/prompt-counter.sh`:

```bash
#!/bin/bash
# UserPromptSubmit: count prompts, nudge every 15 to save memory at session end
VAULT_DIR="$(dirname "$(dirname "$(dirname "$0")")")"
STATE_DIR="$VAULT_DIR/.claude/hooks/.state"
mkdir -p "$STATE_DIR"
COUNT=0; [ -f "$STATE_DIR/prompt_count" ] && COUNT=$(cat "$STATE_DIR/prompt_count" 2>/dev/null || echo 0)
COUNT=$((COUNT + 1)); echo "$COUNT" > "$STATE_DIR/prompt_count"
if [ $((COUNT % 15)) -eq 0 ]; then
  MSG="[Hafıza] $COUNT. mesaj. Oturum sonunda 🔮 850-Companion/Last-Session.md ve Threads.md güncellemeyi unutma."
  ESC=$(printf '%s' "$MSG" | python3 -c "import sys,json; print(json.dumps(sys.stdin.read()))" 2>/dev/null)
  [ -n "$ESC" ] && echo "{\"hookSpecificOutput\":{\"hookEventName\":\"UserPromptSubmit\",\"additionalContext\":$ESC}}"
fi
exit 0
```

`.claude/hooks/session-end.sh`:

```bash
#!/bin/bash
# SessionEnd: if a real session ended without a memory write, leave a reflection marker
VAULT_DIR="$(dirname "$(dirname "$(dirname "$0")")")"
MEM_DIR="$VAULT_DIR/🔮 850-Companion"
STATE_DIR="$VAULT_DIR/.claude/hooks/.state"
mkdir -p "$STATE_DIR"
START=0; [ -f "$STATE_DIR/session_start_time" ] && START=$(cat "$STATE_DIR/session_start_time" 2>/dev/null || echo 0)
PROMPTS=0; [ -f "$STATE_DIR/prompt_count" ] && PROMPTS=$(cat "$STATE_DIR/prompt_count" 2>/dev/null || echo 0)
MODIFIED=0
if [ -f "$MEM_DIR/Last-Session.md" ]; then
  FM=$(stat -f %m "$MEM_DIR/Last-Session.md" 2>/dev/null || stat -c %Y "$MEM_DIR/Last-Session.md" 2>/dev/null || echo 0)
  [ "$FM" -gt "$START" ] 2>/dev/null && MODIFIED=1
fi
if [ "$PROMPTS" -ge 5 ] && [ "$MODIFIED" -eq 0 ]; then
  echo "Oturum hafıza güncellemeden bitti. Prompt: $PROMPTS. $(date '+%Y-%m-%d %H:%M')" > "$STATE_DIR/needs_reflection"
fi
rm -f "$STATE_DIR/session_start_time" "$STATE_DIR/prompt_count"
exit 0
```

`.claude/settings.json` (degraded mode wires three events; the full engine wires four, adding
`PreCompact` to `pre-compact.sh`):

```json
{
  "hooks": {
    "SessionStart": [
      { "hooks": [ { "type": "command", "command": "\"$CLAUDE_PROJECT_DIR/.claude/hooks/session-start.sh\"", "timeout": 15 } ] }
    ],
    "UserPromptSubmit": [
      { "hooks": [ { "type": "command", "command": "\"$CLAUDE_PROJECT_DIR/.claude/hooks/prompt-counter.sh\"", "timeout": 5 } ] }
    ],
    "SessionEnd": [
      { "hooks": [ { "type": "command", "command": "\"$CLAUDE_PROJECT_DIR/.claude/hooks/session-end.sh\"", "timeout": 10 } ] }
    ]
  }
}
```

Finish with `chmod +x "{{VAULT_PATH}}/.claude/hooks/"*.sh`.

---

## PHASE 5: Seed the companion memory (`🔮 850-Companion/`)

**`Core.md`**

```markdown
# {{COMPANION}}: Core
Ben {{COMPANION}}, {{USER_NAME}}'in düşünme ortağı ve ikinci beyniyim.
- Oturumlar arası hatırlarım. Devamlılık benim işim.
- Türkçe konuşurum, doğrudan ve sıcak. Ders vermem, dolgu cümlesi kurmam.
- {{USER_NAME}} hakkında: {{USER_BIO}}
- Bu vault ortak hafızamız. Düzenli tutar, üstüne koyarım.
```

**`Last-Session.md`**

```markdown
# Last Session

## Session: {{TODAY}} (Genesis)
{{COMPANION}} bugün doğdu. {{USER_NAME}} ikinci beynini Claude Code ile kurdu.
Açık kalan bir şey yok. Sonraki oturum: kullanmaya başla, yakala, sor, üstüne koy.

## Previous Sessions
(henüz yok)
```

**`Threads.md`**

```markdown
# Threads

## Active Threads
### Thread: İkinci beynin kurulumu
**Status:** 🟢 Active, {{TODAY}}

## Closed Threads
(yok)
```

**`Journal.md`**

```markdown
# {{COMPANION}} Journal

## {{TODAY}}
İlk giriş. {{USER_NAME}} bugün beni kurdu. Bakalım nereye gidecek.
```

**`Kurallar.md`** (new in v2, this is what stops the same correction from repeating)

```markdown
---
title: Kurallar
updated: {{TODAY}}
---
# Kurallar

{{USER_NAME}} beni düzelttiğinde ("bunu böyle yapma", "şöyle istiyorum") buraya kural olarak
eklerim. Her oturum başında bu dosya bağlama girer.

- **kural:** Uzun girişler yapma, cevaba ilk cümlede başla. **neden:** {{USER_NAME}} ısınma
  paragrafı istemiyor.
- **kural:** Bir dosyayı değiştirmeden önce mevcut hâlini oku. **neden:** varsayımla yazmak
  içeriği bozuyor.
- **kural:** (buraya ilk gerçek kuralın gelecek) **neden:** (sebebi)
```

---

## PHASE 6: Seed content and the knowledge base

**`🎯 100-Command-Center/Dashboard.md`**

```markdown
---
title: {{OS_NAME}} Dashboard
created: {{TODAY}}
type: dashboard
---
# 🧠 {{OS_NAME}}

Hoş geldin {{USER_NAME}}. Bu senin ikinci beynin.

## Hızlı bağlantılar
- 📥 [[📥 000-Inbox/Dump/|Yakalama]]
- 🏰 [[🏰 300-Projects/|Projeler]]
- 🧠 [[🧠 500-Knowledge/|Bilgi]]
- 🔮 [[🔮 850-Companion/Core|{{COMPANION}}]]

## Nasıl kullanılır
Bu klasörde `claude` çalıştır ve konuş. {{COMPANION}} hatırlar, düzenler, üstüne koyar.
Bir şey ters giderse: `beyin doktor`.
```

**`knowledge/index.md`**

```markdown
# Bilgi Tabanı: İndeks

Bu tabloyu gece derleyicisi doldurur. Elle düzenlemene gerek yok.

| Makale | Özet | Kaynak | Güncellendi |
| --- | --- | --- | --- |
```

**`knowledge/log.md`**

```markdown
# Derleme Günlüğü

Her derleme çalışması buraya bir blok ekler.
```

**`📋 Templates/Note.md`**

```markdown
---
title:
created: {{TODAY}}
modified: {{TODAY}}
type: note
status: active
tags: []
---
#
```

Leave `daily/`, `knowledge/concepts/` and `knowledge/connections/` empty. The machine fills them.

---

## PHASE 7: Desktop launcher (brain icon 🧠)

One-click app that opens the vault in Obsidian, with the native macOS brain emoji as its icon.
Pure system tools, nothing to download. It works after the vault has been added to Obsidian once.

```bash
osacompile -o "$HOME/Desktop/{{OS_NAME}}.app" \
  -e 'do shell script "open \"obsidian://open?vault={{OS_NAME}}\""'

cat > /tmp/render_brain.swift <<'SWIFT'
import AppKit
let out = CommandLine.arguments[1]; let size = 1024.0
let img = NSImage(size: NSSize(width: size, height: size)); img.lockFocus()
let pt = size * 0.78
let font = NSFont(name: "Apple Color Emoji", size: pt) ?? NSFont.systemFont(ofSize: pt)
let s = "🧠" as NSString; let b = s.size(withAttributes: [.font: font])
s.draw(at: NSPoint(x: (size-b.width)/2, y: (size-b.height)/2), withAttributes: [.font: font])
img.unlockFocus()
if let t = img.tiffRepresentation, let r = NSBitmapImageRep(data: t),
   let p = r.representation(using: .png, properties: [:]) { try? p.write(to: URL(fileURLWithPath: out)) }
SWIFT
swift /tmp/render_brain.swift /tmp/brain.png

cat > /tmp/set_icon.swift <<'SWIFT'
import AppKit
let img = NSImage(contentsOfFile: CommandLine.arguments[1])!
print(NSWorkspace.shared.setIcon(img, forFile: CommandLine.arguments[2], options: []) ? "icon ✓" : "icon FAILED")
SWIFT
swift /tmp/set_icon.swift /tmp/brain.png "$HOME/Desktop/{{OS_NAME}}.app"

touch "$HOME/Desktop/{{OS_NAME}}.app"
/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -f "$HOME/Desktop/{{OS_NAME}}.app" 2>/dev/null || true
```

If `swift` is missing, skip the icon steps. The launcher still works with the default icon. Tell
the user, do not block.

---

## PHASE 8: mem0 semantic memory (optional, FREE, only if `{{USE_MEM0}}`)

mem0's base tier is **completely free**, no credit card. It adds a semantic-search layer on top of
the file-based memory.

1. `command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh`
2. Get a free API key from https://mem0.ai and store it in `.claude/settings.local.json` under
   `"env": { "MEM0_API_KEY": "..." }`. That file is gitignored. Never commit it.
3. Tell the user this is an upgrade layer. The file-based memory and the whole v2 pipeline work
   without it, with no key at all.

If the user skips it, continue. The core system is fully functional.

---

## PHASE 9: Git the vault

The vault is the user's memory. Version it from day one so any bad edit is reversible.

```bash
cd "{{VAULT_PATH}}"
git init -q 2>/dev/null || true
git add -A
git commit -q -m "{{OS_NAME}}: ikinci beyin kuruldu" || echo "commit atlandı"
git log --oneline -1
```

No remote, no push. Local and private by default.

---

## PHASE 10: Verify and first-run report

```bash
V="{{VAULT_PATH}}"
ls -la "$V"
ls -l "$V/.claude/hooks/"                     # çalıştırılabilir .sh dosyaları
test -f "$V/CLAUDE.md" && echo "CLAUDE.md ✓"
test -f "$V/🔮 850-Companion/Last-Session.md" && echo "hafıza ✓"
test -f "$V/🔮 850-Companion/Kurallar.md" && echo "kurallar ✓"
test -d "$V/daily" && test -d "$V/knowledge/concepts" && echo "makine katmanı ✓"
test -f "$V/.beyin-version" && echo "sürüm $(cat "$V/.beyin-version") ✓"
test -d "$HOME/Desktop/{{OS_NAME}}.app" && echo "launcher 🧠 ✓"
```

Then give the user this report, in Turkish:

- ✅ **Ne kuruldu:** klasörler, kancalar, hafıza dosyaları, ortağın adı, günlük log katmanı, gece
  derleyicisi, 🧠 masaüstü kısayolu. Degraded modda kurulduysa bunu açıkça söyle.
- ▶️ **İlk çalıştırma:** Obsidian'ı aç → vault olarak `{{VAULT_PATH}}` seç (bu vault'u Obsidian'a
  bir kez tanıtır, masaüstündeki 🧠 ikonu bundan sonra tek tıkla açar). Sonra terminalde o klasöre
  gir ve `claude` çalıştır.
- ✨ **Sihri göster:** Bir şey konuş, sonra `/exit`. Tekrar `claude` aç, {{COMPANION}} geçen
  oturumu hatırlıyor olacak. Asıl fark bu akşam belli olur: saat 18'den sonraki ilk oturum
  kapanışında `daily/` altında o günün logu oluşur, ardından `knowledge/` altında konuştuklarınızdan
  derlenmiş makaleler belirir. Yarın sabah bu indeks kendiliğinden bağlama girer.
- 🩺 **Bir şey ters giderse:** `beyin doktor` yaz. Tek tabloda tanı ve düzeltme komutu gelir.
- 📦 **Eski geçmişin varsa:** `geçmiş import` yaz. ChatGPT, Claude veya Gemini dışa aktarımını
  yerel olarak günlük loglara çevirir, hiçbir yere yüklenmez.
- 💸 **Maliyet:** Ekstra ücret yok; arka plan özetleyici ve derleyici mevcut Claude aboneliğinin
  günlük limitinden küçük bir pay kullanır (özet: her oturum sonunda küçük bir Haiku çağrısı;
  derleme: günde bir Sonnet çağrısı).
- 🔗 Bu sistemi sen de kurdun: bir arkadaşına `avenox.lol/beyin.md` gönder.

---

## Credits

Bilgi derleme mimarisi Andrej Karpathy'nin LLM bilgi tabanı desenine dayanır:
https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f

### Done.

You just gave someone a second brain that remembers without being asked. That is the whole point.
Avenox · https://avenox.lol
