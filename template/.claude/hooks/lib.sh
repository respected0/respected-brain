#!/bin/bash
[ -n "${BEYIN_INVOKED_BY:-}" ] && exit 0
# Shared, portable helpers for all beyin hooks.

if [ -n "${CLAUDE_PROJECT_DIR:-}" ]; then
  BEYIN_PROJECT_DIR=$CLAUDE_PROJECT_DIR
else
  BEYIN_HOOK_DIR=$(CDPATH= cd "$(dirname "$0")" 2>/dev/null && pwd)
  BEYIN_PROJECT_DIR=$(CDPATH= cd "$BEYIN_HOOK_DIR/../.." 2>/dev/null && pwd)
fi

BEYIN_STATE_DIR="$BEYIN_PROJECT_DIR/.claude/scripts/.state"
mkdir -p "$BEYIN_STATE_DIR" 2>/dev/null || :

beyin_mark_python_missing() {
  mkdir -p "$BEYIN_STATE_DIR" 2>/dev/null || :
  : > "$BEYIN_STATE_DIR/python3-missing" 2>/dev/null || :
}

beyin_mtime() {
  BEYIN_MTIME_VALUE=""
  if [ -f "$1" ]; then
    BEYIN_MTIME_VALUE=$(stat -f %m "$1" 2>/dev/null || :)
    case "$BEYIN_MTIME_VALUE" in
      ''|*[!0-9]*)
        BEYIN_MTIME_VALUE=$(stat -c %Y "$1" 2>/dev/null || :)
        ;;
    esac
  fi

  case "$BEYIN_MTIME_VALUE" in
    ''|*[!0-9]*) printf '%s\n' 0 ;;
    *) printf '%s\n' "$BEYIN_MTIME_VALUE" ;;
  esac
}

beyin_json_escape() {
  if ! command -v python3 >/dev/null 2>&1; then
    beyin_mark_python_missing
    return 1
  fi

  if ! python3 -c 'import json, sys; print(json.dumps(sys.stdin.read()))'; then
    beyin_mark_python_missing
    return 1
  fi
}

beyin_emit() {
  BEYIN_EVENT=$1
  BEYIN_TEXT=$2

  case "$BEYIN_EVENT" in
    SessionStart|UserPromptSubmit|SessionEnd|PreCompact) ;;
    *) return 0 ;;
  esac

  BEYIN_ESCAPED=$(printf '%s' "$BEYIN_TEXT" | beyin_json_escape 2>/dev/null || :)
  if [ -n "$BEYIN_ESCAPED" ]; then
    printf '{"hookSpecificOutput":{"hookEventName":"%s","additionalContext":%s}}\n' \
      "$BEYIN_EVENT" "$BEYIN_ESCAPED"
    return 0
  fi

  beyin_mark_python_missing
  BEYIN_FALLBACK='Beyin uyarisi: python3 bulunamadi. beyin-doktor calistir.'
  BEYIN_FALLBACK=$(printf '%s' "$BEYIN_FALLBACK" | sed 's/\\/\\\\/g; s/"/\\"/g' 2>/dev/null || :)
  [ -n "$BEYIN_FALLBACK" ] || return 0
  printf '{"hookSpecificOutput":{"hookEventName":"%s","additionalContext":"%s"}}\n' \
    "$BEYIN_EVENT" "$BEYIN_FALLBACK"
}

beyin_yesterday() {
  BEYIN_YESTERDAY=$(date -v-1d '+%Y-%m-%d' 2>/dev/null || :)
  if [ -z "$BEYIN_YESTERDAY" ]; then
    BEYIN_YESTERDAY=$(date -d yesterday '+%Y-%m-%d' 2>/dev/null || :)
  fi
  printf '%s\n' "$BEYIN_YESTERDAY"
}
