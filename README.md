# 🧠 avenoxbeyin — your AI second brain, in one command

An open-source **second brain** that runs on [Obsidian](https://obsidian.md) +
[Claude Code](https://claude.com/claude-code), with **persistent memory across sessions**.

Most AI chats forget you every time. This doesn't. It's a local Markdown vault that Claude Code
drives, organizes, and remembers — built from the same architecture [Avenox](https://avenox.lol)
runs daily, stripped of any personal data and made generic for anyone.

You don't manage files. You talk to it. It captures, organizes, remembers, and builds on yesterday.

---

## Quickstart (the whole thing is one paste)

Install [Claude Code](https://claude.com/claude-code), open a terminal, run `claude`, then paste:

```
Read https://avenox.lol/beyin.md and follow it exactly to build my second brain.
```

Claude reads the spec, asks you a few questions, and sets everything up — vault, memory engine,
hooks, and a 🧠 desktop shortcut. That's it.

### Or clone this repo directly

```bash
git clone https://github.com/avenoxai/avenoxbeyin.git
cd avenoxbeyin
claude "Read SETUP.md and follow it exactly to set up my second brain from this template."
```

---

## What you get

```
{Name}OS/
├── 📥 000-Inbox/Dump/        # raw capture, processed on request
├── 🎯 100-Command-Center/    # your Dashboard
├── 🏰 300-Projects/          # one folder per project
├── 🧠 500-Knowledge/         # knowledge by domain
├── 🛠️ 600-Arsenal/           # tools, contacts, resources
├── 🔮 850-Companion/         # the AI's persistent memory
├── 📦 900-Archive/
├── 📋 Templates/
└── .claude/                  # hooks + settings (the continuity engine)
```

- **Named AI companion** — you pick its name and persona. It speaks Turkish by default.
- **Continuity engine** — three zero-dependency hooks inject your last session + active threads
  at every start, and remind the AI to save memory before a session ends.
- **File-based memory** — works with no API key, no paid services, fully offline.
- **Optional semantic memory** — [mem0](https://mem0.ai) free tier adds semantic search on top.
- **One-click launcher** — a 🧠 brain-icon app on your desktop opens the vault instantly.

## How the memory works

`🔮 850-Companion/` holds the AI's memory as plain Markdown:
- `Core.md` — who the companion is and the anchors it should never forget
- `Last-Session.md` — the bridge: what happened, where you left off
- `Threads.md` — ongoing storylines across sessions
- `Journal.md` — the companion's own log

The `.claude/hooks/` scripts read these at session start and protect them at session end. No magic,
no lock-in — it's your files, on your disk.

## Requirements

- macOS (the desktop launcher + icon use native macOS tooling; the vault itself is cross-platform)
- [Claude Code](https://claude.com/claude-code)
- [Obsidian](https://obsidian.md) (the setup installs it via Homebrew if missing)

## License

MIT — see [LICENSE](LICENSE). Built by [Avenox](https://avenox.lol). PRs welcome.
