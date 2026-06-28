#!/bin/bash
# Second Brain — UserPromptSubmit hook
# Counts prompts; nudges once at 15 to save memory before the session ends.
VAULT_DIR="$(dirname "$(dirname "$(dirname "$0")")")"
STATE_DIR="$VAULT_DIR/.claude/hooks/.state"
mkdir -p "$STATE_DIR"
COUNT=0; [ -f "$STATE_DIR/prompt_count" ] && COUNT=$(cat "$STATE_DIR/prompt_count" 2>/dev/null || echo 0)
COUNT=$((COUNT + 1)); echo "$COUNT" > "$STATE_DIR/prompt_count"
if [ "$COUNT" -eq 15 ]; then
  ESC=$(python3 -c "import json; print(json.dumps('[Memory] Oturum uzadı. Bitirirken 🔮 850-Companion/Last-Session.md ve Threads.md güncellemeyi unutma.'))" 2>/dev/null)
  [ -n "$ESC" ] && echo "{\"hookSpecificOutput\":{\"hookEventName\":\"UserPromptSubmit\",\"additionalContext\":$ESC}}"
fi
exit 0
