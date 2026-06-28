#!/bin/bash
# Second Brain — SessionEnd hook
# If a real session ended without a memory write, leave a reflection marker for next time.
VAULT_DIR="$(dirname "$(dirname "$(dirname "$0")")")"
MEM_DIR="$VAULT_DIR/🔮 850-Companion"
STATE_DIR="$VAULT_DIR/.claude/hooks/.state"
mkdir -p "$STATE_DIR"
START=0; [ -f "$STATE_DIR/session_start_time" ] && START=$(cat "$STATE_DIR/session_start_time" 2>/dev/null || echo 0)
PROMPTS=0; [ -f "$STATE_DIR/prompt_count" ] && PROMPTS=$(cat "$STATE_DIR/prompt_count" 2>/dev/null || echo 0)
MODIFIED=0
if [ -f "$MEM_DIR/Last-Session.md" ]; then
  FM=$(stat -f %m "$MEM_DIR/Last-Session.md" 2>/dev/null || echo 0)
  [ "$FM" -gt "$START" ] 2>/dev/null && MODIFIED=1
fi
if [ "$PROMPTS" -ge 5 ] && [ "$MODIFIED" -eq 0 ]; then
  echo "Oturum hafıza güncellemeden bitti. Prompt: $PROMPTS. $(date '+%Y-%m-%d %H:%M')" > "$STATE_DIR/needs_reflection"
fi
rm -f "$STATE_DIR/session_start_time" "$STATE_DIR/prompt_count"
exit 0
