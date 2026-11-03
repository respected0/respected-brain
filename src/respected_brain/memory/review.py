"""User review of inbox proposals: accept, reject, correct, defer.

Only an explicit user action promotes a note into permanent knowledge. Ledger entries keep
hashes and action history, never note bodies. Model callers cannot review their own proposals.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from ..core.config import atomic_write_text
from ..core.coordination import writer_lease
from ..integrations.notes import create_note, note_path, read_note
from .inbox import MemoryOpError, clean_text
from .provenance import parse_frontmatter, read_provenance

INBOX_PREFIX = "🔮 850-Companion/Inbox/"
PERMANENT_DIR = "🧠 500-Knowledge/Reviewed"
LEDGER_DIR = "memory-review"
MODEL_SOURCES = {"mcp", "orchestrator"}
ACTIONS = {"accept", "reject", "correct", "defer"}
_MAX_BODY = 20_000
_MAX_LEDGER_LINES = 5000
_FRONTMATTER = re.compile(r"\A\ufeff?---[ \t]*\r?\n(.*?)^---[ \t]*(?:\r?\n|$)", re.MULTILINE | re.DOTALL)


def fingerprint(title: str, body: str) -> str:
    text = str(body or "").replace("\r\n", "\n").strip()
    heading = "# " + " ".join(str(title or "").split())
    if text.casefold().startswith(heading.casefold()):
        text = text[len(heading):].lstrip()
    normalized = " ".join(str(title or "").split()).casefold() + "\n" + text
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _title_key(title: str) -> str:
    return " ".join(str(title or "").split()).casefold()[:200]


def _ledger_path(data_root: Path) -> Path:
    return Path(data_root) / LEDGER_DIR / "ledger.jsonl"


def _entries(data_root: Path) -> list[dict[str, Any]]:
    path = _ledger_path(data_root)
    try:
        lines = path.read_text(encoding="utf-8").splitlines()[-_MAX_LEDGER_LINES:]
    except OSError:
        return []
    entries = []
    for line in lines:
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        if isinstance(entry, dict):
            entries.append(entry)
    return entries


def _append(data_root: Path, entry: dict[str, Any]) -> None:
    path = _ledger_path(data_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
        handle.flush()


def proposal_check(data_root: Path, source: str, title: str, body: str) -> dict[str, str]:
    """Block exact re-proposals after rejection; flag repeated titles as learning candidates."""
    if source not in MODEL_SOURCES:
        return {}
    rejects = [entry for entry in _entries(data_root) if entry.get("action") == "reject"]
    digest = fingerprint(title, body)
    if any(entry.get("fingerprint") == digest for entry in rejects):
        raise MemoryOpError("REJECTED_REPROPOSAL", "This proposal was already rejected by the user.",
                            "Wait for an explicit user request before proposing it again.")
    key = _title_key(title)
    if any(entry.get("title_key") == key for entry in rejects):
        return {"review_reason": "repeated-rejection", "learning_candidate": "true"}
    return {}


def _split(content: str) -> tuple[str, str]:
    match = _FRONTMATTER.match(content)
    if not match:
        return "", content
    return content[:match.start(1)], content[match.end():]


def _update(content: str, updates: dict[str, str], *, drop: tuple[str, ...] = ()) -> str:
    match = _FRONTMATTER.match(content)
    rendered = [f"{key}: {json.dumps(str(value), ensure_ascii=False)}" for key, value in updates.items()]
    if not match:
        block = "\n".join(["---", *rendered, "---", ""])
        return block + "\n" + content.lstrip("\r\n") if content else block
    kept = []
    for line in match.group(1).splitlines():
        key = line.partition(":")[0].strip().lower() if line and not line[0].isspace() else ""
        if key in updates or key in drop:
            continue
        kept.append(line)
    return content[:match.start(1)] + "\n".join([*kept, *rendered]) + "\n" + content[match.end(1):]


def _replace_body(content: str, title: str, body: str) -> str:
    match = _FRONTMATTER.match(content)
    document = f"# {title}\n\n{body.replace(chr(13) + chr(10), chr(10)).strip()}\n"
    return content if match is None else content[:match.end()] + document


def _title_of(fields: dict[str, str], body: str, path: Path) -> str:
    if fields.get("title"):
        return fields["title"]
    for line in body.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return path.stem


def _slug(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", title.casefold()).strip("-")[:40] or "note"


def queue(vault_root: Path, data_root: Path, *, include_deferred: bool = False) -> dict[str, Any]:
    """Pending inbox proposals plus learning candidates from repeated rejections."""
    root = Path(vault_root) / "🔮 850-Companion" / "Inbox"
    items = []
    for path in sorted(root.rglob("*.md"))[:1000]:
        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            continue
        fields, body = parse_frontmatter(content)
        provenance = read_provenance(fields)
        status = fields.get("review_status") or provenance["review_status"]
        deferred = fields.get("review") == "deferred"
        if status != "pending" or (deferred and not include_deferred):
            continue
        title = _title_of(fields, body, path)
        items.append({
            "path": path.relative_to(vault_root).as_posix(),
            "title": title,
            "review_status": status,
            "deferred": deferred,
            "review_reason": fields.get("review_reason", ""),
            "learning_candidate": fields.get("learning_candidate") == "true",
            "source_agent": provenance["source_agent"],
            "origin": provenance["origin"],
            "recorded_at": provenance["recorded_at"],
            "fingerprint": fingerprint(title, body),
        })
    counts: dict[str, int] = {}
    for entry in _entries(data_root):
        if entry.get("action") == "reject" and entry.get("title_key"):
            counts[entry["title_key"]] = counts.get(entry["title_key"], 0) + 1
    candidates = [{"title_key": key, "rejections": count} for key, count in counts.items() if count > 1]
    return {"items": items, "learning_candidates": candidates}


def apply(ctx, path: str, action: str, *, corrected_body: str | None = None, corrected_title: str | None = None,
          reason: str = "", until: str = "", operation_id: str = "", reviewer: str = "user") -> dict[str, Any]:
    """Apply one user review action; promotion is the only path into permanent knowledge."""
    if reviewer != "user":
        raise MemoryOpError("MODEL_REVIEW_FORBIDDEN", "A model cannot review or approve its own proposal.",
                            "Ask the user to accept or correct the note.")
    if action not in ACTIONS:
        raise MemoryOpError("BAD_REQUEST", "Unknown review action.", "Use accept, reject, correct or defer.")
    vault = Path(ctx.paths.vault_root)
    target = note_path(vault, path)
    relative = str(path or "").replace("\\", "/")
    if target is None or not relative.startswith(INBOX_PREFIX) or not target.is_file():
        raise MemoryOpError("NOT_FOUND", "No reviewable inbox note at that path.", "")
    content = read_note(vault, relative)
    fields, body = parse_frontmatter(content)
    current = fields.get("review_status") or read_provenance(fields)["review_status"]
    if current in {"approved", "rejected"}:
        raise MemoryOpError("REVIEW_ALREADY_FINAL", "That note was already reviewed.", "")
    title = _title_of(fields, body, target)
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    updates = {"reviewed_at": now, "reviewed_by": "user", "review_action": action}
    drop: tuple[str, ...] = ()
    write_body: str | None = None

    if action == "defer":
        updates.update({"review": "deferred", "review_deferred_at": now, "review_status": "pending"})
        if until:
            updates["review_deferred_until"] = until[:10]
    elif action == "reject":
        updates.update({"review_status": "rejected", "review_reason": "user-rejected"})
        drop = ("review_deferred_at", "review_deferred_until")
    else:
        if action == "correct":
            if not isinstance(corrected_body, str) or not corrected_body.strip() or len(corrected_body) > _MAX_BODY:
                raise MemoryOpError("BAD_REQUEST", "Correction needs a non-empty body up to 20000 characters.", "")
            if corrected_title is not None:
                new_title = clean_text(corrected_title)
                if not 1 <= len(new_title) <= 120:
                    raise MemoryOpError("BAD_REQUEST", "Invalid correction title.", "Use 1-120 characters.")
                updates["title"] = new_title
                title = new_title
            write_body = corrected_body.replace("\r\n", "\n").strip()
            updates["source_sha256"] = hashlib.sha256(write_body.encode("utf-8")).hexdigest()
        updates.update({"review_status": "approved", "origin": "user_approved"})
        drop = ("review_deferred_at", "review_deferred_until", "review")

    updated = _update(content, updates, drop=drop)
    if write_body is not None:
        updated = _replace_body(updated, title, write_body)
    promoted_to = ""
    before = hashlib.sha256(content.encode("utf-8")).hexdigest()
    with writer_lease(ctx):
        if action in {"accept", "correct"}:
            _, final_body = _split(updated)
            permanent = _update(updated, {
                "promoted_from": relative,
                "promoted_at": now,
                "review_status": "approved",
                "origin": "user_approved",
            })
            directory = vault / PERMANENT_DIR
            filename = f"{dt.date.today():%Y-%m-%d}-{_slug(title)}-{fingerprint(title, final_body)[:8]}.md"
            try:
                created = create_note(vault, directory, filename, permanent)
            except FileExistsError:
                existing = directory / filename
                if existing.read_text(encoding="utf-8") != permanent:
                    raise MemoryOpError("PROMOTION_CONFLICT", "A different note already exists at the promotion path.", "") from None
                created = existing
            promoted_to = created.relative_to(vault).as_posix()
            updated = _update(updated, {"promoted_to": promoted_to})
        atomic_write_text(target, updated)
        after = hashlib.sha256(updated.encode("utf-8")).hexdigest()
        rejects = [entry for entry in _entries(ctx.paths.data_root)
                   if entry.get("action") == "reject" and entry.get("title_key") == _title_key(title)]
        learning = action == "reject" and bool(rejects)
        if learning:
            updated = _update(target.read_text(encoding="utf-8"), {"learning_candidate": "true"})
            atomic_write_text(target, updated)
            after = hashlib.sha256(updated.encode("utf-8")).hexdigest()
        _append(ctx.paths.data_root, {
            "at": now,
            "action": action,
            "path": relative,
            "operation_id": operation_id,
            "before_sha256": before,
            "after_sha256": after,
            "promoted_to": promoted_to,
            "fingerprint": fingerprint(title, write_body if write_body is not None else body),
            "title_key": _title_key(title),
            "reason": clean_text(reason, 200),
            "learning_candidate": learning,
            "reviewer": "user",
        })
    return {"action": action, "path": relative, "review_status": "rejected" if action == "reject" else
            ("pending" if action == "defer" else "approved"), "promoted_to": promoted_to,
            "learning_candidate": learning, "reviewed_at": now}