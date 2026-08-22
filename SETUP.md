# SETUP.md v2: Activate this second brain (Claude Code runbook)

> You are Claude Code, run from inside a freshly cloned `avenoxbeyin` repo. The user wants their
> own AI second brain, or wants to upgrade the one they already have. The scaffold lives in
> `./template/`. Your job: decide the mode, interview the user, install or upgrade, verify.
> Execute phase by phase. Speak **Turkish** to the user (the audience is Turkish). This runbook is
> in English only so your instructions stay precise; the system you build talks Turkish.

## Rules (binding)

1. **Interview first, build second.** Nothing touches the filesystem before PHASE 0.
2. **Never destroy.** If a target file or folder exists, show it and ask. Default to merge or
   skip, never a silent clobber. In upgrade mode this is absolute: existing memory files are
   read-only for you.
3. **Resolve every `{{PLACEHOLDER}}`.** Never leave a literal `{{...}}` in any written file.
4. **Don't block on optional steps** (obsidian-cli, mem0, swift icon). Log it, tell the user,
   continue.
5. **Verify each phase** with a quick check before moving on. End with the first-run report.
6. **Be the demo.** This is often filmed. Narrate what you are doing in short Turkish lines as you
   go: "Vault iskeletini kuruyorum...", "Hafıza motorunu bağlıyorum...", "Derleyiciyi yerine
   koyuyorum...". Short sentences, no walls of text.
7. **Everything is free.** No API key is required anywhere. The background summarizer and the
   compiler run on the user's existing Claude subscription through `claude -p`.

Placeholders you must resolve:
`{{OS_NAME}}` · `{{USER_NAME}}` · `{{USER_BIO}}` · `{{COMPANION}}` · `{{VAULT_PATH}}` ·
`{{SCOPE}}` · `{{USE_MEM0}}` · `{{TODAY}}`

| Placeholder | Nereden gelir | Örnek |
| --- | --- | --- |
| `{{OS_NAME}}` | makine adından türetilir, kullanıcı onaylar | `AylinOS` |
| `{{USER_NAME}}` | soru 1 | `Aylin` |
| `{{USER_BIO}}` | soru 2, 1 veya 2 cümle | `Ürün tasarımcısı, yan projeler yürütüyor` |
| `{{COMPANION}}` | soru 3, AI ortağının adı | `Echo` |
| `{{VAULT_PATH}}` | PHASE 0.3 | `~/Documents/AylinOS` |
| `{{SCOPE}}` | soru 4, opsiyonel klasörler | `core+goals` |
| `{{USE_MEM0}}` | soru 5 | `evet` |
| `{{TODAY}}` | `date +%F` | `2026-08-22` |

`{{SCOPE}}` ve `{{USE_MEM0}}` dosya içine yazılmaz, sadece hangi klasörlerin ve hangi opsiyonel
adımın çalışacağını belirler. Diğer altısı dosya içeriklerinde geçer.

---

## PHASE M: Mode selection (do this FIRST, before anything else)

Ask the user in Turkish: **"Daha önce kurulmuş bir beynin var mı? Varsa klasör yolunu ver."**
If they say no, still scan the two default locations before deciding:

```bash
for D in "$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents"/* "$HOME/Documents"/*; do
  [ -d "$D" ] || continue
  if [ -f "$D/CLAUDE.md" ] && ls -d "$D/🔮 850-"* >/dev/null 2>&1; then
    echo "ADAY: $D"
    if [ -f "$D/.beyin-version" ]; then
      echo "  sürüm: $(cat "$D/.beyin-version")"
    else
      echo "  sürüm: v1 (.beyin-version yok)"
    fi
  fi
done
```

Decide:

| Bulgu | Mod |
| --- | --- |
| Aday yok | **MODE A, sıfırdan kurulum** (PHASE 0'a git) |
| Aday var, `.beyin-version` yok | **MODE B, v1'den yükseltme** (PHASE U0'a git) |
| Aday var, `.beyin-version` = `2.0.0` | Zaten v2. Sadece `beyin-doktor` çalıştır, eksikleri kapat |
| Aday var, `.beyin-version` başka bir değer | Kullanıcıya göster, ne yapılacağını sor |

Tell the user which mode you picked and why, in one Turkish sentence. Never guess silently.

---

# MODE A: Fresh install

## PHASE 0: Interview

Detect the machine name and derive the OS name:

```bash
scutil --get ComputerName 2>/dev/null || hostname
```

PascalCase it and append `OS` (strip "MacBook/Pro/Air/iMac/'s", apostrophes, dashes).
`Johns-MacBook-Pro` → `JohnOS`, `aylin's Mac` → `AylinOS`, `DESKTOP-AB12` → `Ab12OS`.
Propose `{{OS_NAME}}`, let the user override.

Ask (Turkish, conversational, not a form):

1. **İsmin ne?** → `{{USER_NAME}}`
2. **Ne iş yapıyorsun, bu beyni en çok ne için kullanacaksın?** → `{{USER_BIO}}`
3. **AI ortağına ne isim vermek istersin?** → `{{COMPANION}}`
4. **Kapsam:** core (herkes) + opsiyonel `⚔️ 200-Goals`, `🔐 400-Vault`, `💪 700-Body`,
   `🧘 800-Mind` → `{{SCOPE}}`
5. **Semantik hafıza (mem0)?** Temel sürümü **ücretsiz** (mem0.ai, kredi kartı yok). Dosya
   tabanlı hafıza onsuz da tam çalışır, mem0 üstüne anlamsal arama katar. Önerilir. →
   `{{USE_MEM0}}`

Pick the vault path → `{{VAULT_PATH}}`:

- If `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/` exists → `.../Documents/{{OS_NAME}}`
- Else → `~/Documents/{{OS_NAME}}`

Confirm the path with the user. Set `{{TODAY}}` = `date +%F`.

## PHASE 1: Prerequisites

```bash
command -v brew >/dev/null || /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
ls "/Applications/Obsidian.app" >/dev/null 2>&1 || brew install --cask obsidian
# obsidian-cli (optional, never block)
command -v obsidian >/dev/null 2>&1 || (brew tap yakitrak/yakitrak 2>/dev/null && brew install yakitrak/yakitrak/obsidian-cli 2>/dev/null) || echo "obsidian-cli atlandı (opsiyonel)"
```

**v2 hard requirement, check it now:**

```bash
command -v python3 >/dev/null && python3 -V || echo "PYTHON3 YOK"
command -v claude  >/dev/null && echo "claude CLI ✓" || echo "CLAUDE CLI YOK"
```

`python3` is what the background summarizer and the compiler run on. It ships with macOS Command
Line Tools; if it is missing, tell the user in Turkish that the automatic memory layer will stay
off until they install it (`xcode-select --install`), and continue. Never fail silently.

## PHASE 2: Place the vault

```bash
mkdir -p "$(dirname "{{VAULT_PATH}}")"
cp -R "./template/" "{{VAULT_PATH}}/"
chmod +x "{{VAULT_PATH}}/.claude/hooks/"*.sh
```

Create only the optional scope folders the user picked in `{{SCOPE}}`:
`⚔️ 200-Goals` · `🔐 400-Vault` · `💪 700-Body` · `🧘 800-Mind`

Verify the v2 pieces landed:

```bash
cd "{{VAULT_PATH}}"
ls .claude/hooks/          # session-start.sh prompt-counter.sh session-end.sh pre-compact.sh lib.sh
ls .claude/scripts/        # flush.py compile.py
ls .claude/skills/         # beyin-doktor gecmis-import
ls -d daily knowledge/concepts knowledge/connections
cat .beyin-version         # 2.0.0
```

## PHASE 3: Personalize (substitute placeholders)

Replace EVERY placeholder in EVERY file under `{{VAULT_PATH}}` with the resolved values, then
verify none remain:

```bash
grep -rl "{{" "{{VAULT_PATH}}" || echo "✓ tüm placeholder'lar dolduruldu"
```

Also update the structure section of `CLAUDE.md` to list any optional scope folders you created.
The memory folder stays `🔮 850-Companion` even when the companion has a name: the hooks and the
scripts reference that fixed path. The persona name lives in the file *contents*, not in the
folder name. Say this to the user in one line so it does not look like a bug.

## PHASE 4: Git (new in v2)

The vault is the user's memory. Version it from day one, so an upgrade or a bad edit is always
reversible.

```bash
cd "{{VAULT_PATH}}"
git init -q 2>/dev/null || true
git add -A
git -c user.name="{{USER_NAME}}" -c user.email="beyin@localhost" commit -q -m "{{OS_NAME}}: ikinci beyin kuruldu" || echo "commit atlandı"
git log --oneline -1
```

If the user already has a global git identity, use it and drop the `-c` flags. Do not create any
remote, do not push anywhere. This repo is local and private by default.

## PHASE 5: Desktop launcher (brain icon 🧠)

One-click app that opens the vault in Obsidian, with the native macOS brain emoji as its icon.
Pure system tools, nothing to download. Works after the vault is added to Obsidian once (PHASE 8).

```bash
# 1) launcher applet
osacompile -o "$HOME/Desktop/{{OS_NAME}}.app" \
  -e 'do shell script "open \"obsidian://open?vault={{OS_NAME}}\""'

# 2) render 🧠 to PNG (Swift + AppKit, present on every Mac with Command Line Tools)
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

# 3) set as app icon (writes the custom Icon resource, overrides the default applet icon)
cat > /tmp/set_icon.swift <<'SWIFT'
import AppKit
let img = NSImage(contentsOfFile: CommandLine.arguments[1])!
print(NSWorkspace.shared.setIcon(img, forFile: CommandLine.arguments[2], options: []) ? "icon ✓" : "icon FAILED")
SWIFT
swift /tmp/set_icon.swift /tmp/brain.png "$HOME/Desktop/{{OS_NAME}}.app"

# 4) refresh Finder
touch "$HOME/Desktop/{{OS_NAME}}.app"
/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -f "$HOME/Desktop/{{OS_NAME}}.app" 2>/dev/null || true
```

If `swift` is missing, skip steps 2 and 3; the launcher still works with a default icon.

## PHASE 6: mem0 semantic memory (optional, FREE, only if `{{USE_MEM0}}` is yes)

1. `command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh`
2. Free API key from https://mem0.ai, stored in `{{VAULT_PATH}}/.claude/settings.local.json`:
   `{ "env": { "MEM0_API_KEY": "..." } }`. That file is already gitignored. Never commit it.
3. Tell the user it is an upgrade layer. The file-based memory and the whole v2 pipeline work
   without it, with no key at all.

## PHASE 7: First doctor run

```bash
cd "{{VAULT_PATH}}" && claude "beyin doktor"
```

The `beyin-doktor` skill prints one health table. Close every 🔴 row before you report success.
If the doctor cannot run for any reason, do the manual check instead:

```bash
cd "{{VAULT_PATH}}"
ls -l .claude/hooks/*.sh | awk '{print $1, $NF}'   # hepsi çalıştırılabilir olmalı
python3 -c "import json;d=json.load(open('.claude/settings.json'));print(sorted(d.get('hooks',{})))"
python3 -m py_compile .claude/scripts/flush.py .claude/scripts/compile.py && echo "scriptler ✓"
```

## PHASE 8: Verify and first-run report

```bash
ls -la "{{VAULT_PATH}}"
test -f "{{VAULT_PATH}}/CLAUDE.md" && echo "CLAUDE.md ✓"
test -f "{{VAULT_PATH}}/🔮 850-Companion/Last-Session.md" && echo "hafıza ✓"
test -f "{{VAULT_PATH}}/.beyin-version" && echo "sürüm $(cat "{{VAULT_PATH}}/.beyin-version") ✓"
test -d "$HOME/Desktop/{{OS_NAME}}.app" && echo "launcher 🧠 ✓"
```

Then jump to **THE DEMO** at the bottom of this file.

---

# MODE B: Upgrade an existing v1 vault to v2

> The user already has a working brain. Their memory files are the whole point of it. This mode is
> **additive only**. You add the machine layer, replace the four hook scripts, merge the settings,
> and touch nothing else.

## The upgrade contract (read it out loud to yourself before you type)

**NEVER touch:**
- `🔮 850-Companion/*.md` (or whatever the memory folder is named): Core, Last-Session, Threads,
  Journal. Not a rewrite, not a reformat, not a "small cleanup". Kurallar.md is seeded **only if
  it does not exist**.
- `🎯 100-Command-Center/Dashboard.md` and every other note the user or the companion wrote.
- `CLAUDE.md`. It carries the user's personalization. You may *append* a short v2 section at the
  end if the user says yes, and only then.
- `.claude/settings.local.json` secrets (`env`, API keys).

**ADD (only if absent):**
- `daily/`, `knowledge/`, `knowledge/concepts/`, `knowledge/connections/` with their `.gitkeep`s
- `knowledge/index.md`, `knowledge/log.md`
- `.claude/scripts/` (flush.py, compile.py, `.state/`)
- `.claude/skills/beyin-doktor/`, `.claude/skills/gecmis-import/`
- `🔮 850-Companion/Kurallar.md`
- `.beyin-version`
- `.gitignore` entries that are missing

**REPLACE:**
- `.claude/hooks/*.sh` and `.claude/hooks/lib.sh`. These are code, not memory. The v2 versions are
  strict supersets of v1 behavior.

**MERGE, idempotently:**
- `.claude/settings.json` hook wiring. An event that is already wired to the same hook file is
  skipped, never duplicated. Running the upgrade twice must produce the exact same file.

## PHASE U0: Pin the target and snapshot it

```bash
V="<kullanıcının vault yolu>"          # tırnak içinde tut, boşluk ve emoji var
cd "$V" && pwd
ls -d "🔮 850-"* 2>/dev/null
ls .claude/hooks/ 2>/dev/null
cat .claude/settings.json 2>/dev/null
cat .claude/settings.local.json 2>/dev/null | python3 -c "import sys,json;d=json.load(sys.stdin);print('anahtarlar:',sorted(d))" 2>/dev/null
```

Snapshot before anything changes:

```bash
cd "$V"
if [ -d .git ]; then
  git add -A && git commit -q -m "v2 yükseltmesi öncesi anlık görüntü" || echo "değişiklik yok, commit atlandı"
else
  git init -q && git add -A && git commit -q -m "v2 yükseltmesi öncesi anlık görüntü" || echo "git atlandı"
fi
git log --oneline -1
```

If git is unavailable, make a copy instead and tell the user where it is:
`cp -R "$V" "$V.yedek-$(date +%F)"`.

## PHASE U1: Memory folder name check

v1 vaults built from the public spec sometimes have the memory folder named after the companion
(`🔮 850-Echo`) instead of the fixed `🔮 850-Companion`. The v2 hooks and scripts read the fixed
path, so a renamed folder means the memory injection silently stops working.

```bash
cd "$V"; ls -d "🔮 850-"*
```

If it is not exactly `🔮 850-Companion`, **ask the user** and offer two options in Turkish:

1. **Önerilen:** klasörü `🔮 850-Companion` olarak yeniden adlandır. İçerik hiç değişmez, sadece
   klasör adı değişir; ortağın ismi zaten dosyaların içinde yazıyor.
   `git mv "🔮 850-Echo" "🔮 850-Companion"` (git yoksa `mv`).
2. Klasör adı kalsın. Bu durumda v2'nin hafıza enjeksiyonu bu vault'ta çalışmaz, `beyin-doktor`
   bunu her seferinde 🔴 olarak gösterir.

Never rename without an explicit yes. Never copy the contents into a new folder and delete the old
one; a rename is a rename.

## PHASE U2: Add the machine layer (additive, idempotent)

Run from the repo root, with `$V` still pointing at the vault:

```bash
R="$(pwd)"                              # avenoxbeyin repo kökü

# klasörler
mkdir -p "$V/daily" "$V/knowledge/concepts" "$V/knowledge/connections" \
         "$V/.claude/scripts/.state" "$V/.claude/skills"
for K in "$V/daily/.gitkeep" "$V/knowledge/concepts/.gitkeep" \
         "$V/knowledge/connections/.gitkeep" "$V/.claude/scripts/.state/.gitkeep"; do
  [ -f "$K" ] || : > "$K"
done

# scriptler (kod, üzerine yazılır)
cp "$R/template/.claude/scripts/flush.py"   "$V/.claude/scripts/flush.py"
cp "$R/template/.claude/scripts/compile.py" "$V/.claude/scripts/compile.py"

# skill'ler (kod, üzerine yazılır)
cp -R "$R/template/.claude/skills/beyin-doktor"  "$V/.claude/skills/"
cp -R "$R/template/.claude/skills/gecmis-import" "$V/.claude/skills/"

# seed dosyaları: SADECE yoksa
for S in "knowledge/index.md" "knowledge/log.md" "🔮 850-Companion/Kurallar.md"; do
  if [ -f "$V/$S" ]; then
    echo "atlandı (zaten var): $S"
  else
    cp "$R/template/$S" "$V/$S" && echo "eklendi: $S"
  fi
done

# sürüm damgası
printf '2.0.0\n' > "$V/.beyin-version"
```

Then resolve the placeholders **in the newly copied files only**:

```bash
grep -rl "{{" "$V/knowledge" "$V/.claude/skills" "$V/🔮 850-Companion/Kurallar.md" 2>/dev/null
```

Read `CLAUDE.md` and the existing memory files to recover the user's name and the companion's
name, and fill the new files with those. Do not ask the user to repeat what the vault already
knows; confirm your reading in one line instead: "Ortağının adı X, senin adın Y, doğru mu?"

## PHASE U3: Replace the hooks

```bash
cp "$R/template/.claude/hooks/lib.sh"            "$V/.claude/hooks/lib.sh"
cp "$R/template/.claude/hooks/session-start.sh"  "$V/.claude/hooks/session-start.sh"
cp "$R/template/.claude/hooks/prompt-counter.sh" "$V/.claude/hooks/prompt-counter.sh"
cp "$R/template/.claude/hooks/session-end.sh"    "$V/.claude/hooks/session-end.sh"
cp "$R/template/.claude/hooks/pre-compact.sh"    "$V/.claude/hooks/pre-compact.sh"
chmod +x "$V/.claude/hooks/"*.sh
for H in "$V/.claude/hooks/"*.sh; do bash -n "$H" && echo "syntax ✓ $(basename "$H")"; done
```

If the old hooks had user edits, the pre-upgrade snapshot in PHASE U0 holds them. Say so.

## PHASE U4: Merge the hook wiring, idempotently

v2 reads `.claude/settings.json`. Merge, do not overwrite: keep every key the user already has,
add only the missing hook entries.

```bash
python3 - "$V" "$R" <<'PY'
import json, os, sys
vault, repo = sys.argv[1], sys.argv[2]
dst = os.path.join(vault, ".claude", "settings.json")
src = os.path.join(repo, "template", ".claude", "settings.json")

with open(src, encoding="utf-8") as f:
    wanted = json.load(f).get("hooks", {})
try:
    with open(dst, encoding="utf-8") as f:
        cur = json.load(f)
except (FileNotFoundError, ValueError):
    cur = {}
cur.setdefault("hooks", {})

def cmds(matchers):
    out = []
    for m in matchers:
        for h in m.get("hooks", []):
            out.append(h.get("command", ""))
    return out

added = 0
for event, matchers in wanted.items():
    have = cmds(cur["hooks"].setdefault(event, []))
    for m in matchers:
        new = [c for c in cmds([m]) if not any(os.path.basename(c.strip('"')) in h for h in have)]
        if new:
            cur["hooks"][event].append(m)
            added += 1
with open(dst, "w", encoding="utf-8") as f:
    json.dump(cur, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("eklenen kanca girdisi:", added)
PY
```

Run it twice on purpose. The second run must print `eklenen kanca girdisi: 0`. That is the
idempotency proof; show it to the user.

**Duplicate wiring check.** v1 vaults built from the public spec wired the hooks in
`settings.local.json` instead. If both files wire the same hook, it fires twice per event:

```bash
python3 - "$V" <<'PY'
import json, os, sys
p = os.path.join(sys.argv[1], ".claude", "settings.local.json")
try:
    with open(p, encoding="utf-8") as f:
        d = json.load(f)
except (FileNotFoundError, ValueError):
    d = {}
print("settings.local.json kanca içeriyor mu:", "hooks" in d, "| diğer anahtarlar:",
      sorted(k for k in d if k != "hooks"))
PY
```

If it does, **ask the user** before touching it, then remove only the `hooks` key and keep
everything else (the mem0 key lives in `env`):

```bash
cp "$V/.claude/settings.local.json" "$V/.claude/settings.local.json.yedek"
python3 - "$V" <<'PY'
import json, os, sys
p = os.path.join(sys.argv[1], ".claude", "settings.local.json")
with open(p, encoding="utf-8") as f:
    d = json.load(f)
d.pop("hooks", None)
with open(p, "w", encoding="utf-8") as f:
    json.dump(d, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("kalan anahtarlar:", sorted(d))
PY
```

## PHASE U5: Merge .gitignore, append only

```bash
for L in ".claude/settings.local.json" ".claude/hooks/.state/" ".claude/scripts/.state/*" \
         "!.claude/scripts/.state/.gitkeep" ".DS_Store"; do
  grep -qxF "$L" "$V/.gitignore" 2>/dev/null || printf '%s\n' "$L" >> "$V/.gitignore"
done
cat "$V/.gitignore"
```

## PHASE U6: Doctor, commit, optional history import

```bash
cd "$V" && claude "beyin doktor"
```

Close every 🔴 row. Then commit the upgrade:

```bash
cd "$V" && git add -A && git commit -q -m "v2'ye yükseltildi" && git log --oneline -2
```

Optional, offer it in one Turkish line, do not push it: **"Eski ChatGPT, Claude veya Gemini
geçmişini de bu beyne aktarmak ister misin? `geçmiş import` yeter."** The `gecmis-import` skill
does everything locally; nothing is uploaded anywhere. Large exports take several evenings to
compile, and that is fine.

Then jump to **THE DEMO**.

---

# THE DEMO (both modes end here)

Report in Turkish:

- ✅ **Ne kuruldu:** klasörler, 4 kanca, arka plan özetleyici, gece derleyicisi, hafıza dosyaları,
  ortağın adı, 🧠 masaüstü kısayolu. Yükseltme modunda: hangi dosyalara dokunulmadığını da say.
- ▶️ **İlk çalıştırma:** Obsidian'ı aç → vault olarak `{{VAULT_PATH}}` seç (bir kez tanıtır,
  masaüstündeki 🧠 ikonu bundan sonra tek tıkla açar). Sonra o klasörde `claude` çalıştır.
- ✨ **Sihri göster:** Bir şey konuş → `/exit` → tekrar `claude`. Ortağın geçen oturumu
  hatırlıyor olacak. Bu v1'de de vardı. v2'nin farkı şu: bu akşam saat 18'den sonraki ilk
  oturum kapanışında `daily/` klasöründe o günün logu oluşur, sonra `knowledge/` altında
  konuştuklarınızdan derlenmiş makaleler belirir. Yarın sabah `claude` açtığında bu bilgi tabanının
  indeksi kendiliğinden bağlama girer. Kimse hiçbir şey yazmayı hatırlamak zorunda değil.
- 🩺 **Bir şey ters giderse:** `beyin doktor` yaz. Tek tabloda her parçanın durumunu verir.
- 💸 **Maliyet:** Ekstra ücret yok; arka plan özetleyici ve derleyici mevcut Claude aboneliğinin
  günlük limitinden küçük bir pay kullanır (özet: her oturum sonunda küçük bir Haiku çağrısı;
  derleme: günde bir Sonnet çağrısı).
- 🔗 **Sen de kurdun mu?** Bir arkadaşına gönder: `avenox.lol/beyin.md`

Do not end the session by saying "kuruldu" alone. Show the pipeline once, with the user watching.

---

Done. You just gave someone a second brain that remembers without being asked.
Avenox · https://avenox.lol
