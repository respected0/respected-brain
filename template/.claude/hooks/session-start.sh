#!/bin/bash
# Second Brain — Session Start hook
# Injects continuity (last session bridge + active threads) at the start of every session.
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

REFLECTION=""
if [ -f "$STATE_DIR/needs_reflection" ]; then
  REFLECTION="⚠️ Önceki oturum hafıza güncellemeden bitti: $(cat "$STATE_DIR/needs_reflection"). Anlamlı bir şey olduysa 🔮 850-Companion dosyalarını güncelle."
  rm -f "$STATE_DIR/needs_reflection"
fi

CTX=""
[ -n "$REFLECTION" ] && CTX="${CTX}${REFLECTION}\n\n"
[ -n "$LAST_SESSION" ] && CTX="${CTX}[Memory — Last Session]\n${LAST_SESSION}\n\n"
[ -n "$THREADS" ] && CTX="${CTX}[Memory — Active Threads]\n${THREADS}\n\n"
CTX="${CTX}[Memory] Continuity is your job. Read 🔮 850-Companion/Core.md for who you are to this user."

if [ -n "$CTX" ]; then
  ESC=$(printf '%s' "$CTX" | python3 -c "import sys,json; print(json.dumps(sys.stdin.read()))" 2>/dev/null)
  [ -n "$ESC" ] && echo "{\"hookSpecificOutput\":{\"hookEventName\":\"SessionStart\",\"additionalContext\":${ESC}}}"
fi
exit 0
