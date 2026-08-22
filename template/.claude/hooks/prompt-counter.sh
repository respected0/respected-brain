#!/bin/bash
[ -n "${BEYIN_INVOKED_BY:-}" ] && exit 0
# Count prompts and nudge at every multiple of fifteen.

BEYIN_HOOK_DIR=$(CDPATH= cd "$(dirname "$0")" 2>/dev/null && pwd)
. "$BEYIN_HOOK_DIR/lib.sh" 2>/dev/null || exit 0

BEYIN_COUNT=0
if [ -f "$BEYIN_STATE_DIR/prompt_count" ]; then
  BEYIN_COUNT=$(sed -n '1p' "$BEYIN_STATE_DIR/prompt_count" 2>/dev/null || :)
fi
case "$BEYIN_COUNT" in
  ''|*[!0-9]*) BEYIN_COUNT=0 ;;
esac

BEYIN_COUNT=$((BEYIN_COUNT + 1))
printf '%s\n' "$BEYIN_COUNT" > "$BEYIN_STATE_DIR/prompt_count" 2>/dev/null || :

if [ $((BEYIN_COUNT % 15)) -eq 0 ]; then
  beyin_emit UserPromptSubmit "[Hafıza] $BEYIN_COUNT. mesaj. Oturum sonunda 🔮 850-Companion/Last-Session.md ve Threads.md güncellemeyi unutma."
fi
exit 0
