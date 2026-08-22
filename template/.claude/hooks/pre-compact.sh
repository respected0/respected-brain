#!/bin/bash
[ -n "${BEYIN_INVOKED_BY:-}" ] && exit 0
# Detach a pre-compaction flush without changing live session state.

BEYIN_HOOK_DIR=$(CDPATH= cd "$(dirname "$0")" 2>/dev/null && pwd)
. "$BEYIN_HOOK_DIR/lib.sh" 2>/dev/null || exit 0

BEYIN_HOOK_INPUT="$BEYIN_STATE_DIR/hookin-$$.json"
umask 077
if ! cat > "$BEYIN_HOOK_INPUT" 2>/dev/null; then
  rm -f "$BEYIN_HOOK_INPUT" 2>/dev/null || :
  BEYIN_HOOK_INPUT=""
fi

if [ -n "$BEYIN_HOOK_INPUT" ]; then
  if command -v python3 >/dev/null 2>&1; then
    nohup python3 "$BEYIN_PROJECT_DIR/.claude/scripts/flush.py" \
      --hook-input "$BEYIN_HOOK_INPUT" --reason precompact >/dev/null 2>&1 &
  else
    beyin_mark_python_missing
    rm -f "$BEYIN_HOOK_INPUT" 2>/dev/null || :
    beyin_emit PreCompact 'Beyin sıkıştırma öncesi özeti başlatılamadı: python3 bulunamadı. beyin-doktor çalıştır.'
  fi
fi
exit 0
