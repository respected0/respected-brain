#!/bin/bash
[ -n "${BEYIN_INVOKED_BY:-}" ] && exit 0
# Mark relational-memory debt, then detach the automatic session flush.

BEYIN_HOOK_DIR=$(CDPATH= cd "$(dirname "$0")" 2>/dev/null && pwd)
. "$BEYIN_HOOK_DIR/lib.sh" 2>/dev/null || exit 0

BEYIN_HOOK_INPUT="$BEYIN_STATE_DIR/hookin-$$.json"
umask 077
if ! cat > "$BEYIN_HOOK_INPUT" 2>/dev/null; then
  rm -f "$BEYIN_HOOK_INPUT" 2>/dev/null || :
  BEYIN_HOOK_INPUT=""
fi

BEYIN_MEMORY_DIR="$BEYIN_PROJECT_DIR/🔮 850-Companion"
BEYIN_START=0
BEYIN_PROMPTS=0
[ -f "$BEYIN_STATE_DIR/session_start_time" ] && BEYIN_START=$(sed -n '1p' "$BEYIN_STATE_DIR/session_start_time" 2>/dev/null || :)
[ -f "$BEYIN_STATE_DIR/prompt_count" ] && BEYIN_PROMPTS=$(sed -n '1p' "$BEYIN_STATE_DIR/prompt_count" 2>/dev/null || :)
case "$BEYIN_START" in ''|*[!0-9]*) BEYIN_START=0 ;; esac
case "$BEYIN_PROMPTS" in ''|*[!0-9]*) BEYIN_PROMPTS=0 ;; esac

BEYIN_MODIFIED=0
if [ -f "$BEYIN_MEMORY_DIR/Last-Session.md" ]; then
  BEYIN_FILE_MTIME=$(beyin_mtime "$BEYIN_MEMORY_DIR/Last-Session.md")
  case "$BEYIN_FILE_MTIME" in ''|*[!0-9]*) BEYIN_FILE_MTIME=0 ;; esac
  [ "$BEYIN_FILE_MTIME" -gt "$BEYIN_START" ] 2>/dev/null && BEYIN_MODIFIED=1
fi

if [ "$BEYIN_PROMPTS" -ge 5 ] && [ "$BEYIN_MODIFIED" -eq 0 ]; then
  printf 'Oturum hafıza güncellemeden bitti. Prompt: %s. %s\n' \
    "$BEYIN_PROMPTS" "$(date '+%Y-%m-%d %H:%M' 2>/dev/null)" \
    > "$BEYIN_STATE_DIR/needs_reflection" 2>/dev/null || :
fi

if [ -n "$BEYIN_HOOK_INPUT" ]; then
  if command -v python3 >/dev/null 2>&1; then
    nohup python3 "$BEYIN_PROJECT_DIR/.claude/scripts/flush.py" \
      --hook-input "$BEYIN_HOOK_INPUT" >/dev/null 2>&1 &
  else
    beyin_mark_python_missing
    rm -f "$BEYIN_HOOK_INPUT" 2>/dev/null || :
    beyin_emit SessionEnd 'Beyin arka plan özeti başlatılamadı: python3 bulunamadı. beyin-doktor çalıştır.'
  fi
fi

rm -f "$BEYIN_STATE_DIR/session_start_time" "$BEYIN_STATE_DIR/prompt_count" 2>/dev/null || :
exit 0
