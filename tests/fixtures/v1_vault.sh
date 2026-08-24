#!/usr/bin/env bash
# Shared fixture: build a realistic v1 vault for upgrade regression tests.
#
# Contract (both upgrade test suites depend on this, do not change silently):
#   make_v1_vault <dst-abs> [--no-git] [--memory-dir NAME] [--clean-local] [--bad-local]
#
# Default vault contains:
#   .claude/settings.json         v1 wiring for 3 events (no PreCompact in v1)
#   .claude/settings.local.json   MEM0_API_KEY + one v1 SessionEnd hook + one unrelated
#                                 Notification hook + a permissions block
#   .claude/hooks/*.sh            three v1 hooks
#   "🔮 850-Companion"/           memory notes (renamed to a v1-era name on request)
#   daily/2026-01-02.md           one daily entry
#   .env                          a secret that must never be staged
#   git repo with one commit unless --no-git
#
# Flags:
#   --no-git          skip git init entirely (forces the external-backup path)
#   --memory-dir NAME use NAME as the memory folder (e.g. "🔮 850-Echo") to force a rename
#   --clean-local     write settings.local.json with NO beyin hooks (only unrelated ones)
#   --bad-local       write a settings.local.json that is valid JSON but not an object
set -euo pipefail

# Hermeticity: the developer's own global gitignore may already ignore
# .claude/settings.local.json (it does on at least one machine). If tests inherit that,
# "the upgrade protects the secret" goes green for the wrong reason and would be red on a
# clean machine. Neutralise global and system git config for everything these tests run,
# including scripts/upgrade.sh, which shells out to git itself.
# GIT_CONFIG_GLOBAL alone is NOT enough: ~/.config/git/ignore is git's XDG *default*
# excludes path, used when core.excludesFile is unset, so blanking the global config file
# does not disable it. Override the key itself through the environment so every git process
# in the test, including the ones scripts/upgrade.sh spawns, sees an empty excludes file.
export GIT_CONFIG_GLOBAL=/dev/null
export GIT_CONFIG_SYSTEM=/dev/null
export GIT_CONFIG_COUNT=1
export GIT_CONFIG_KEY_0=core.excludesFile
export GIT_CONFIG_VALUE_0=/dev/null

make_v1_vault() {
  local dst="$1"; shift
  local use_git=1 mem="🔮 850-Companion" local_mode="dirty"
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --no-git)      use_git=0; shift ;;
      --memory-dir)  mem="$2"; shift 2 ;;
      --clean-local) local_mode="clean"; shift ;;
      --bad-local)   local_mode="bad"; shift ;;
      *) printf 'make_v1_vault: bilinmeyen bayrak: %s\n' "$1" >&2; return 2 ;;
    esac
  done

  mkdir -p "$dst/.claude/hooks/.state" "$dst/$mem" "$dst/daily" \
           "$dst/🎯 100-Command-Center" "$dst/📥 000-Inbox/Dump"

  # --- v1 hooks (bodies only need to be recognisable and executable)
  local h
  for h in session-start session-end prompt-counter; do
    cat > "$dst/.claude/hooks/$h.sh" <<HOOK
#!/usr/bin/env bash
# v1 $h hook (kullanıcının elindeki eski sürüm)
echo '{}'
HOOK
    chmod +x "$dst/.claude/hooks/$h.sh"
  done

  # --- a hook the user wrote themselves; the upgrade must not touch it
  cat > "$dst/.claude/hooks/kullanici-kendi.sh" <<'HOOK'
#!/usr/bin/env bash
# Kullanıcının kendi yazdığı kanca. Yükseltme buna dokunmamalı.
echo '{}'
HOOK
  chmod +x "$dst/.claude/hooks/kullanici-kendi.sh"

  # --- v1 settings.json
  cat > "$dst/.claude/settings.json" <<'JSON'
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
JSON

  # --- settings.local.json
  case "$local_mode" in
    dirty)
      cat > "$dst/.claude/settings.local.json" <<'JSON'
{
  "env": { "MEM0_API_KEY": "m0-GIZLI-ANAHTAR-ASLA-COMMITLENMEZ" },
  "permissions": { "allow": ["Bash(git status)"] },
  "hooks": {
    "SessionEnd": [
      { "hooks": [ { "type": "command", "command": "\"$CLAUDE_PROJECT_DIR/.claude/hooks/session-end.sh\"", "timeout": 10 } ] }
    ],
    "Notification": [
      { "matcher": "*", "hooks": [ { "type": "command", "command": "/usr/local/bin/bildirim-sesi.sh", "timeout": 5 } ] }
    ]
  }
}
JSON
      ;;
    clean)
      cat > "$dst/.claude/settings.local.json" <<'JSON'
{
  "env": { "MEM0_API_KEY": "m0-GIZLI-ANAHTAR-ASLA-COMMITLENMEZ" },
  "permissions": { "allow": ["Bash(git status)"] },
  "hooks": {
    "Notification": [
      { "matcher": "*", "hooks": [ { "type": "command", "command": "/usr/local/bin/bildirim-sesi.sh", "timeout": 5 } ] }
    ]
  }
}
JSON
      ;;
    bad)
      printf '%s\n' '["bu bir liste, nesne degil"]' > "$dst/.claude/settings.local.json"
      ;;
  esac

  # --- vault content
  printf '# Core\n\nKullanıcının kendi notu.\n'          > "$dst/$mem/Core.md"
  printf '# Son Oturum\n\nv1 içeriği.\n'                  > "$dst/$mem/Last-Session.md"
  printf '# Konular\n\nv1 içeriği.\n'                     > "$dst/$mem/Threads.md"
  printf '# Journal\n\nv1 içeriği.\n'                     > "$dst/$mem/Journal.md"
  printf '# 2 Ocak 2026\n\n- ilk gün\n'                   > "$dst/daily/2026-01-02.md"
  printf '# Dashboard\n\nv1.\n'                           > "$dst/🎯 100-Command-Center/Dashboard.md"
  printf '# CLAUDE\n\nv1 yönlendirici.\n'                 > "$dst/CLAUDE.md"
  printf 'ANTHROPIC_API_KEY=sk-GIZLI-ASLA-COMMITLENMEZ\n' > "$dst/.env"
  : > "$dst/📥 000-Inbox/Dump/.gitkeep"

  if [ "$use_git" = "1" ]; then
    git -C "$dst" init -q
    git -C "$dst" config user.name  "Test Kullanici"
    git -C "$dst" config user.email "test@localhost"
    printf '.env\n' > "$dst/.gitignore"
    git -C "$dst" add -A
    git -C "$dst" -c commit.gpgsign=false commit -q -m "v1 vault"
  fi
}
