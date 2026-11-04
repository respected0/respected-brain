"""Read-only memory insights: skill suggestions, opt-in session search, handoff context, vault health.

Nothing here writes to the vault or the archive. Suggestions stay advisory until a human acts.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..core.resources import ResourceCatalog
from ..maintenance.tiling_check import check_tiling, tokenize
from ..maintenance.vault_linter import lint_vault
from . import decisions as decision_lifecycle
from . import events as memory_events
from .context import build_context
from .redact import redact
from .review import LEDGER_DIR
from .untrusted import inert

ARCHIVE_SUBDIR = Path("archives") / "agent-history"
_MAX_QUERY = 200
_MAX_ARCHIVE_FILES = 200
_MAX_ARCHIVE_LINES = 20000
_MAX_LINE = 2000
_MAX_SUGGESTIONS = 20


def _normalized(text: str) -> str:
    return " ".join(str(text or "").split()).casefold()


def _skill_catalog() -> list[dict[str, Any]]:
    catalog = ResourceCatalog()
    skills: list[dict[str, Any]] = []
    try:
        names = catalog.iter_files("skills")
    except (FileNotFoundError, NotADirectoryError):
        return skills
    for name in names:
        if not name.endswith("/SKILL.md"):
            continue
        try:
            text = catalog.read_text("skills/" + name)
        except OSError:
            continue
        title = name.split("/")[0]
        description = ""
        for line in text.splitlines()[1:12]:
            if line.startswith("description:"):
                description = line.partition(":")[2].strip()
                break
        skills.append({
            "name": title,
            "description": description,
            "tokens": tokenize(title + " " + description),
        })
    return skills


def _ledger_candidates(data_root: Path) -> list[dict[str, str]]:
    path = Path(data_root) / LEDGER_DIR / "ledger.jsonl"
    try:
        lines = path.read_text(encoding="utf-8").splitlines()[-5000:]
    except OSError:
        return []
    candidates: list[dict[str, str]] = []
    for line in lines:
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        if not isinstance(entry, dict) or entry.get("learning_candidate") is not True:
            continue
        title = str(entry.get("title_key") or "").strip()
        if title:
            candidates.append({"title": title, "reason": "repeated-rejection", "source": "review-ledger"})
    return candidates


def skill_suggestions(data_root: Path, vault_root: Path | None = None, *, limit: int = 10) -> dict[str, Any]:
    """Suggest which existing skill to consult, or a new skill to consider, from rejected proposals and learnings."""
    limit = max(0, min(int(limit), _MAX_SUGGESTIONS))
    candidates = _ledger_candidates(data_root)
    try:
        events = memory_events.list_events(vault_root, include_archive=True) if vault_root else []
    except OSError:
        events = []
    seen = {_normalized(item["title"]) for item in candidates}
    for event in events:
        for learning in event.get("learnings") or []:
            text = str(learning or "").strip()
            if text and _normalized(text) not in seen:
                seen.add(_normalized(text))
                candidates.append({"title": text, "reason": "session-learning", "source": str(event.get("id") or "")})
    skills = _skill_catalog()
    suggestions = []
    for candidate in candidates[:limit]:
        tokens = tokenize(candidate["title"])
        best = None
        best_overlap = 0
        for skill in skills:
            overlap = len(tokens & skill["tokens"])
            if overlap > best_overlap:
                best, best_overlap = skill, overlap
        matched = best["name"] if best is not None and best_overlap >= 2 else ""
        suggestions.append({
            "title": candidate["title"],
            "reason": candidate["reason"],
            "source": candidate["source"],
            "matching_skill": matched,
            "action": "use-existing-skill" if matched else "consider-new-skill",
        })
    return {"count": len(candidates), "suggestions": suggestions, "truncated": len(candidates) > len(suggestions)}


def session_search(data_root: Path, query: str, *, limit: int = 10) -> dict[str, Any]:
    """Search the opt-in redacted agent archive only; bounded, never follows links, never writes."""
    text = " ".join(str(query or "").split())
    if not 2 <= len(text) <= _MAX_QUERY:
        raise ValueError(f"query must be 2-{_MAX_QUERY} characters")
    limit = max(0, min(int(limit), 20))
    if limit == 0:
        return {"query": text, "count": 0, "results": [], "truncated": False}
    root = Path(data_root).resolve() / ARCHIVE_SUBDIR
    if not root.is_dir():
        return {"query": text, "count": 0, "results": [], "truncated": False}
    files = sorted(
        (path for path in root.iterdir() if path.is_file() and path.suffix == ".jsonl" and not path.is_symlink()),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )[:_MAX_ARCHIVE_FILES]
    needle = text.casefold()
    results: list[dict[str, Any]] = []
    scanned = 0
    truncated = False
    for path in files:
        if not path.resolve().is_relative_to(root):
            continue
        agent = path.stem.split("_", 1)[0] or "unknown"
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for number, line in enumerate(lines, 1):
            scanned += 1
            if scanned > _MAX_ARCHIVE_LINES:
                truncated = True
                break
            if needle not in line.casefold():
                continue
            snippet = inert(redact(line[:_MAX_LINE]))
            results.append({"agent": agent, "file": path.name, "line": number, "snippet": snippet})
            if len(results) >= limit:
                truncated = len(results) >= limit
                break
        if truncated:
            break
    return {"query": text, "count": len(results), "results": results, "truncated": truncated}


def handoff_context(vault_root: Path, *, provider: str | None = None, budget_tokens: int = 600) -> dict[str, Any]:
    """A bounded, provider-aware handoff: latest session, open work, active and disputed decisions."""
    events = memory_events.list_events(vault_root, include_archive=True)
    if provider:
        events = [event for event in events if str(event.get("provider") or "") == provider]
    if not events:
        empty = build_context([], budget_tokens=budget_tokens)
        return {"provider": provider, "providers": [], "latest_event_id": "", "context": empty,
                "text": empty["text"], "tokens": empty["tokens"], "budget_tokens": empty["budget_tokens"],
                "truncated": empty["truncated"]}
    latest = events[-1]
    latest_by_provider: dict[str, dict[str, Any]] = {}
    for event in events:
        latest_by_provider[str(event.get("provider") or "unknown")] = event
    records = decision_lifecycle.collect(events)
    active = decision_lifecycle.current(records)
    review = decision_lifecycle.review_items(records)
    threads: dict[str, dict[str, Any]] = {}
    for event in events:
        for thread in event.get("threads") or []:
            if isinstance(thread, dict) and thread.get("title"):
                threads[str(thread["title"])] = thread
    open_threads = [thread for thread in threads.values() if thread.get("status") != "completed"]
    items: list[dict[str, Any]] = []
    for name, event in latest_by_provider.items():
        snippet = redact(str(event.get("context") or "")).strip()
        if snippet:
            items.append({"path": f"provider:{name}", "title": f"Son {name} oturumu",
                          "snippet": inert(" ".join(snippet.split())[:600])})
    for record in active[:5]:
        items.append({"path": f"decision:{record['id']}", "title": "Aktif karar",
                      "snippet": redact(record["text"])[:300]})
    for record in review[:5]:
        items.append({"path": f"review:{record['id']}", "title": f"İnceleme: {record['review_reason']}",
                      "snippet": redact(record["text"])[:300]})
    for thread in open_threads[:5]:
        summary = " ".join(str(thread.get("summary") or "").split())
        items.append({"path": f"thread:{thread['title']}", "title": f"Konu: {thread['title']}",
                      "snippet": redact(summary)[:300]})
    for todo in latest.get("todos") or []:
        value = str(todo or "").strip()
        if value:
            items.append({"path": f"todo:{value[:40]}", "title": "Açık iş", "snippet": redact(value)[:300]})
    context = build_context(items, budget_tokens=budget_tokens)
    return {
        "provider": provider,
        "providers": sorted(latest_by_provider),
        "latest_event_id": str(latest.get("id") or ""),
        "context": context,
        "text": context["text"],
        "tokens": context["tokens"],
        "budget_tokens": context["budget_tokens"],
        "truncated": context["truncated"],
    }


def health_report(vault_root: Path, *, threshold: float = 0.55, limit: int = 10) -> dict[str, Any]:
    """One bounded report: duplicate pairs, decision conflicts, and lint counts."""
    limit = max(1, min(int(limit), 50))
    tiling = check_tiling(vault_root, threshold)
    lint = lint_vault(vault_root)
    records = decision_lifecycle.collect(memory_events.list_events(vault_root, include_archive=True))
    review = decision_lifecycle.review_items(records)
    duplicates = tiling["duplicate_pairs_count"]
    lint_healthy = bool(lint.get("is_healthy"))
    return {
        "healthy": duplicates == 0 and not review and lint_healthy,
        "duplicates": {"count": duplicates, "top": tiling["pairs"][:limit]},
        "conflicts": {
            "count": len(review),
            "top": [{"id": item["id"], "text": redact(item["text"]), "status": item["status"],
                     "review_reason": item["review_reason"]} for item in review[:limit]],
        },
        "lint": {
            "is_healthy": lint_healthy,
            "total_markdown_files": lint["total_markdown_files"],
            "dead_links_count": lint["dead_links_count"],
            "orphan_pages_count": lint["orphan_pages_count"],
            "frontmatter_issues_count": lint["frontmatter_issues_count"],
            "filename_issues_count": lint["filename_issues_count"],
            "freshness_warnings_count": lint["freshness_warnings_count"],
            "top_dead_links": lint["dead_links"][:limit],
        },
    }