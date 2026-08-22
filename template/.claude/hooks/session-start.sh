#!/bin/bash
[ -n "${BEYIN_INVOKED_BY:-}" ] && exit 0
# Inject relational memory, rules, recent journal context, and the knowledge index.

BEYIN_HOOK_DIR=$(CDPATH= cd "$(dirname "$0")" 2>/dev/null && pwd)
. "$BEYIN_HOOK_DIR/lib.sh" 2>/dev/null || exit 0

BEYIN_MEMORY_DIR="$BEYIN_PROJECT_DIR/🔮 850-Companion"
mkdir -p "$BEYIN_STATE_DIR" 2>/dev/null || :
date '+%s' > "$BEYIN_STATE_DIR/session_start_time" 2>/dev/null || :
printf '%s\n' 0 > "$BEYIN_STATE_DIR/prompt_count" 2>/dev/null || :

BEYIN_LAST_SESSION=""
if [ -f "$BEYIN_MEMORY_DIR/Last-Session.md" ]; then
  BEYIN_LAST_SESSION=$(awk '
    /^## Session:/ { active = 1 }
    active && /^## Previous/ { exit }
    active { print }
  ' "$BEYIN_MEMORY_DIR/Last-Session.md" 2>/dev/null | sed -n '1,50p')
fi

BEYIN_THREADS=""
if [ -f "$BEYIN_MEMORY_DIR/Threads.md" ]; then
  BEYIN_THREADS=$(sed -n '/^## Active/,/^## Closed/p' "$BEYIN_MEMORY_DIR/Threads.md" 2>/dev/null \
    | grep -E '^### |^\*\*Status:\*\*' 2>/dev/null \
    | sed -n '1,12p')
fi

BEYIN_RULES=""
if [ -f "$BEYIN_MEMORY_DIR/Kurallar.md" ]; then
  BEYIN_RULES=$(sed -n '1,60p' "$BEYIN_MEMORY_DIR/Kurallar.md" 2>/dev/null)
fi

BEYIN_JOURNAL=""
if [ -f "$BEYIN_MEMORY_DIR/Journal.md" ]; then
  BEYIN_JOURNAL_LINE=$(grep -n '^## ' "$BEYIN_MEMORY_DIR/Journal.md" 2>/dev/null \
    | tail -n 1 | cut -d: -f1)
  case "$BEYIN_JOURNAL_LINE" in
    ''|*[!0-9]*) ;;
    *)
      BEYIN_JOURNAL_END=$((BEYIN_JOURNAL_LINE + 9))
      BEYIN_JOURNAL=$(sed -n "${BEYIN_JOURNAL_LINE},${BEYIN_JOURNAL_END}p" \
        "$BEYIN_MEMORY_DIR/Journal.md" 2>/dev/null)
      ;;
  esac
fi

BEYIN_INDEX=""
if [ -f "$BEYIN_PROJECT_DIR/knowledge/index.md" ]; then
  BEYIN_INDEX=$(sed -n '1,150p' "$BEYIN_PROJECT_DIR/knowledge/index.md" 2>/dev/null)
fi

BEYIN_DAILY=""
BEYIN_TODAY=$(date '+%Y-%m-%d' 2>/dev/null || :)
BEYIN_DAILY_FILE=""
if [ -n "$BEYIN_TODAY" ] && [ -f "$BEYIN_PROJECT_DIR/daily/$BEYIN_TODAY.md" ]; then
  BEYIN_DAILY_FILE="$BEYIN_PROJECT_DIR/daily/$BEYIN_TODAY.md"
else
  BEYIN_YESTERDAY=$(beyin_yesterday)
  if [ -n "$BEYIN_YESTERDAY" ] && [ -f "$BEYIN_PROJECT_DIR/daily/$BEYIN_YESTERDAY.md" ]; then
    BEYIN_DAILY_FILE="$BEYIN_PROJECT_DIR/daily/$BEYIN_YESTERDAY.md"
  fi
fi
[ -n "$BEYIN_DAILY_FILE" ] && BEYIN_DAILY=$(tail -n 25 "$BEYIN_DAILY_FILE" 2>/dev/null)

BEYIN_REFLECTION=""
if [ -f "$BEYIN_STATE_DIR/needs_reflection" ]; then
  BEYIN_REFLECTION="⚠️ Önceki oturum hafıza güncellemeden bitti: $(sed -n '1p' "$BEYIN_STATE_DIR/needs_reflection" 2>/dev/null). Anlamlı bir şey olduysa 🔮 850-Companion dosyalarını güncelle."
  rm -f "$BEYIN_STATE_DIR/needs_reflection" 2>/dev/null || :
fi

BEYIN_NL='
'
BEYIN_TRUNCATED=0
BEYIN_CLOSING='[Hafıza] Süreklilik senin sorumluluğun. Bu kullanıcı için kim olduğunu anlamak üzere 🔮 850-Companion/Core.md dosyasını oku.
Hafıza protokolü zorunludur.'
BEYIN_TRUNCATION_NOTE='[not: indeks kırpıldı — beyin-doktor çalıştır]'

beyin_build_context() {
  BEYIN_CONTEXT=""
  [ -n "$BEYIN_REFLECTION" ] && BEYIN_CONTEXT="${BEYIN_CONTEXT}${BEYIN_REFLECTION}${BEYIN_NL}${BEYIN_NL}"
  [ -n "$BEYIN_LAST_SESSION" ] && BEYIN_CONTEXT="${BEYIN_CONTEXT}[Hafıza — Son Oturum]${BEYIN_NL}${BEYIN_LAST_SESSION}${BEYIN_NL}${BEYIN_NL}"
  [ -n "$BEYIN_THREADS" ] && BEYIN_CONTEXT="${BEYIN_CONTEXT}[Hafıza — Aktif Konular]${BEYIN_NL}${BEYIN_THREADS}${BEYIN_NL}${BEYIN_NL}"
  [ -n "$BEYIN_RULES" ] && BEYIN_CONTEXT="${BEYIN_CONTEXT}[Hafıza — Kurallar]${BEYIN_NL}${BEYIN_RULES}${BEYIN_NL}${BEYIN_NL}"
  [ -n "$BEYIN_JOURNAL" ] && BEYIN_CONTEXT="${BEYIN_CONTEXT}[Hafıza — Son Journal]${BEYIN_NL}${BEYIN_JOURNAL}${BEYIN_NL}${BEYIN_NL}"
  [ -n "$BEYIN_INDEX" ] && BEYIN_CONTEXT="${BEYIN_CONTEXT}[Bilgi Tabanı — İndeks]${BEYIN_NL}${BEYIN_INDEX}${BEYIN_NL}${BEYIN_NL}"
  [ -n "$BEYIN_DAILY" ] && BEYIN_CONTEXT="${BEYIN_CONTEXT}[Bugünün Logu]${BEYIN_NL}${BEYIN_DAILY}${BEYIN_NL}${BEYIN_NL}"
  [ "$BEYIN_TRUNCATED" -eq 1 ] && BEYIN_CONTEXT="${BEYIN_CONTEXT}${BEYIN_TRUNCATION_NOTE}${BEYIN_NL}${BEYIN_NL}"
  BEYIN_CONTEXT="${BEYIN_CONTEXT}${BEYIN_CLOSING}"
}

beyin_build_context
if [ "${#BEYIN_CONTEXT}" -gt 16000 ]; then
  BEYIN_TRUNCATED=1
  beyin_build_context

  BEYIN_OVER=$(( ${#BEYIN_CONTEXT} - 16000 ))
  if [ "$BEYIN_OVER" -gt 0 ] && [ -n "$BEYIN_INDEX" ]; then
    if [ "$BEYIN_OVER" -ge "${#BEYIN_INDEX}" ]; then
      BEYIN_INDEX=""
    else
      BEYIN_KEEP=$(( ${#BEYIN_INDEX} - BEYIN_OVER ))
      BEYIN_INDEX=${BEYIN_INDEX:0:$BEYIN_KEEP}
    fi
    beyin_build_context
  fi

  BEYIN_OVER=$(( ${#BEYIN_CONTEXT} - 16000 ))
  if [ "$BEYIN_OVER" -gt 0 ] && [ -n "$BEYIN_DAILY" ]; then
    if [ "$BEYIN_OVER" -ge "${#BEYIN_DAILY}" ]; then
      BEYIN_DAILY=""
    else
      BEYIN_DAILY=${BEYIN_DAILY:$BEYIN_OVER}
    fi
    beyin_build_context
  fi

  # Journal and reflection are the only remaining non-protected sections.
  BEYIN_OVER=$(( ${#BEYIN_CONTEXT} - 16000 ))
  if [ "$BEYIN_OVER" -gt 0 ] && [ -n "$BEYIN_JOURNAL" ]; then
    if [ "$BEYIN_OVER" -ge "${#BEYIN_JOURNAL}" ]; then
      BEYIN_JOURNAL=""
    else
      BEYIN_KEEP=$(( ${#BEYIN_JOURNAL} - BEYIN_OVER ))
      BEYIN_JOURNAL=${BEYIN_JOURNAL:0:$BEYIN_KEEP}
    fi
    beyin_build_context
  fi

  BEYIN_OVER=$(( ${#BEYIN_CONTEXT} - 16000 ))
  if [ "$BEYIN_OVER" -gt 0 ] && [ -n "$BEYIN_REFLECTION" ]; then
    if [ "$BEYIN_OVER" -ge "${#BEYIN_REFLECTION}" ]; then
      BEYIN_REFLECTION=""
    else
      BEYIN_KEEP=$(( ${#BEYIN_REFLECTION} - BEYIN_OVER ))
      BEYIN_REFLECTION=${BEYIN_REFLECTION:0:$BEYIN_KEEP}
    fi
    beyin_build_context
  fi
fi

[ -n "$BEYIN_CONTEXT" ] && beyin_emit SessionStart "$BEYIN_CONTEXT"
exit 0
