# SETUP.md — Activate this second brain (Claude Code runbook)

> You are Claude Code, run from inside a freshly cloned `avenoxbeyin` repo. The user wants their
> own AI second brain. The scaffold already exists in `./template/`. Your job: interview the user,
> copy the scaffold to its real home, personalize it, install prerequisites, and create a desktop
> launcher. Execute phase by phase. Speak **Turkish** to the user (audience is Turkish).

## Rules
1. Interview first, build second. Never leave a literal `{{...}}` placeholder in any file.
2. Never destroy. If the target vault path already exists, show it and ask before overwriting.
3. Don't block on optional steps (obsidian-cli, mem0, swift icon). Log, tell the user, continue.
4. Verify each phase. End with the first-run report.

Placeholders to resolve: `{{OS_NAME}}` · `{{USER_NAME}}` · `{{USER_BIO}}` · `{{COMPANION}}` ·
`{{VAULT_PATH}}` · `{{TODAY}}`

---

## PHASE 0 — Interview

Detect the machine name and derive the OS name:
```bash
scutil --get ComputerName 2>/dev/null || hostname
```
PascalCase it + append `OS` (strip "MacBook/Pro/Air/iMac/'s"). `Johns-MacBook-Pro` → `JohnOS`.
Propose `{{OS_NAME}}`, let the user override.

Ask (Turkish, conversational):
1. **İsmin ne?** → `{{USER_NAME}}`
2. **Ne iş yapıyorsun / bu beyni en çok ne için kullanacaksın?** → `{{USER_BIO}}`
3. **AI ortağına ne isim vermek istersin?** → `{{COMPANION}}`
4. **Kapsam:** core (herkes) + opsiyonel `⚔️ 200-Goals`, `🔐 400-Vault`, `💪 700-Body`, `🧘 800-Mind`
5. **Semantik hafıza (mem0)?** Temel sürümü **ücretsiz** (mem0.ai, kredi kartı yok). Önerilir.

Pick the vault path → `{{VAULT_PATH}}`:
- If `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/` exists → `.../Documents/{{OS_NAME}}`
- Else → `~/Documents/{{OS_NAME}}`
Confirm with the user. Set `{{TODAY}}` = `date +%F`.

---

## PHASE 1 — Prerequisites
```bash
command -v brew >/dev/null || /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
ls "/Applications/Obsidian.app" >/dev/null 2>&1 || brew install --cask obsidian
# obsidian-cli (optional)
command -v obsidian >/dev/null 2>&1 || (brew tap yakitrak/yakitrak 2>/dev/null && brew install yakitrak/yakitrak/obsidian-cli 2>/dev/null) || echo "obsidian-cli atlandı (opsiyonel)"
```

---

## PHASE 2 — Place the vault
Copy the scaffold to its real home (don't overwrite an existing vault without asking):
```bash
mkdir -p "$(dirname "{{VAULT_PATH}}")"
cp -R "./template/" "{{VAULT_PATH}}/"
chmod +x "{{VAULT_PATH}}/.claude/hooks/"*.sh
```
Create optional scope folders the user picked (only those):
`⚔️ 200-Goals` · `🔐 400-Vault` · `💪 700-Body` · `🧘 800-Mind`

---

## PHASE 3 — Personalize (substitute placeholders)
Replace EVERY placeholder in EVERY file under `{{VAULT_PATH}}` with the resolved values.
Files with placeholders: `CLAUDE.md`, `🎯 100-Command-Center/Dashboard.md`, and all of
`🔮 850-Companion/*.md`. Then verify none remain:
```bash
grep -rl "{{" "{{VAULT_PATH}}" || echo "✓ tüm placeholder'lar dolduruldu"
```
Also update the structure section of `CLAUDE.md` to list any optional scope folders you created.
If the user named the companion something specific, you may keep the folder as `🔮 850-Companion`
(the hooks reference that fixed path) — the persona name lives in the file *contents*, not the
folder name.

---

## PHASE 4 — Desktop launcher (brain icon 🧠)
One-click app that opens the vault in Obsidian, with the native macOS brain emoji as its icon.
Pure system tools, nothing to download. (Works after the vault is added to Obsidian once — PHASE 6.)
```bash
# 1) launcher applet
osacompile -o "$HOME/Desktop/{{OS_NAME}}.app" \
  -e 'do shell script "open \"obsidian://open?vault={{OS_NAME}}\""'

# 2) render 🧠 to PNG (Swift + AppKit — present on every Mac with Command Line Tools)
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

# 3) set as app icon (writes the custom Icon resource — overrides the default applet icon)
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
If `swift` is missing, skip steps 2–3; the launcher still works with a default icon.

---

## PHASE 5 — mem0 semantic memory (recommended, FREE — only if the user opted in)
1. `command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh`
2. Free API key from https://mem0.ai → store in `{{VAULT_PATH}}/.claude/settings.local.json`:
   `{ "env": { "MEM0_API_KEY": "..." } }`. This file is already gitignored — never commit it.
3. Tell the user it's an upgrade; the file-based memory already works without it.

---

## PHASE 6 — Verify & first-run report
```bash
ls -la "{{VAULT_PATH}}"
test -f "{{VAULT_PATH}}/CLAUDE.md" && echo "CLAUDE.md ✓"
test -f "{{VAULT_PATH}}/🔮 850-Companion/Last-Session.md" && echo "memory ✓"
test -d "$HOME/Desktop/{{OS_NAME}}.app" && echo "launcher 🧠 ✓"
```
Report in Turkish:
- ✅ Ne kuruldu (klasörler, hooks, hafıza, companion adı, 🧠 masaüstü kısayolu)
- ▶️ **İlk çalıştırma:** Obsidian'ı aç → vault olarak `{{VAULT_PATH}}` seç (bir kez tanıtır;
  masaüstündeki 🧠 ikonu bundan sonra tek tıkla açar). Sonra o klasörde `claude` çalıştır.
- ✨ **Sihri göster:** Bir şey konuş → `/exit` → tekrar `claude`. {{COMPANION}} geçen oturumu
  hatırlıyor olacak. Devamlılık = fark.
- 🔗 Sen de kurdun mu? Bir arkadaşına gönder: `avenox.lol/beyin.md`

---
Done. You just gave someone a second brain that remembers. — Avenox · https://avenox.lol
