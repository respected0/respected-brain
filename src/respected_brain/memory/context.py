"""Task-based, token-budgeted progressive memory context.

Stage one returns a compact, prioritized view of search hits. The agent expands a
hit through the existing bounded note readers; this module never reads or writes
the vault.
"""

from __future__ import annotations

import math
from typing import Any

DEFAULT_BUDGET_TOKENS = 600
MAX_BUDGET_TOKENS = 4000


def estimate_tokens(text: str) -> int:
    """Rough token estimate (four characters per token) used for budgeting."""
    return max(1, math.ceil(len(text) / 4)) if text else 0


def _clip(text: str, limit: int) -> str:
    if limit <= 0:
        return ""
    if len(text) <= limit:
        return text
    cut = text[:limit]
    space = cut.rfind(" ")
    if space > 0:
        cut = cut[:space]
    return cut.rstrip(" ,;:.") + "\u2026"


def build_context(
    results: list[dict[str, Any]],
    *,
    budget_tokens: int = DEFAULT_BUDGET_TOKENS,
    detail: str = "summary",
) -> dict[str, Any]:
    """Return ranked hits as compact text within a token budget.

    ``detail="short"`` keeps only title and path; ``"summary"`` adds the
    query-focused snippet. The full note is always a separate reader call.
    """
    if detail not in {"short", "summary"}:
        raise ValueError("detail must be 'short' or 'summary'")
    try:
        budget = int(budget_tokens)
    except (TypeError, ValueError):
        raise ValueError("budget_tokens must be an integer") from None
    budget = max(1, min(budget, MAX_BUDGET_TOKENS))
    limit_chars = budget * 4

    lines: list[str] = []
    items: list[dict[str, Any]] = []
    used = 0
    truncated = False
    for hit in results:
        path = str(hit.get("path") or "").strip()
        title = str(hit.get("title") or path).strip()
        if not path:
            continue
        snippet = "" if detail == "short" else " ".join(str(hit.get("snippet") or "").split())
        head = f"- **{title}** (`{path}`)"
        line = head if not snippet else f"{head} \u2014 {snippet}"
        separator = 1 if lines else 0
        remaining = limit_chars - used - separator
        shown = snippet
        if len(line) > remaining:
            truncated = True
            room = remaining - len(head) - 4
            if room < 24:
                break
            shown = _clip(snippet, room)
            line = f"{head} \u2014 {shown}"
        if len(line) > remaining:
            truncated = True
            break
        lines.append(line)
        items.append({"path": path, "title": title, "snippet": shown})
        used += len(line) + separator

    text = "\n".join(lines)
    return {
        "detail": detail,
        "text": text,
        "tokens": estimate_tokens(text),
        "budget_tokens": budget,
        "items": items,
        "truncated": truncated,
        "expand": [item["path"] for item in items],
    }
