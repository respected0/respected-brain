"""RPP memory workspace ops for the Hub: `memory.search`, `memory.note.read`, `memory.capture.note`, `memory.briefing.run`.

These are the user's own actions (no grant token). The Hub's webview bridge blocks every `memory.*` op, so only the Hub's
trusted commands reach them. Search shares the read-only, hash-verified pipeline of `memory.recall`; notes are only read or
created inside the active vault through the same bounded note I/O the MCP server uses.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import time
from pathlib import Path
from typing import Any

from ..core.config import atomic_write_json
from ..core.coordination import writer_lease
from ..core.errors import BusyError
from ..integrations.notes import create_note, note_path, read_note
from .integrations import _context
from .memory import MemoryOpError, _active_vault_id, _bad, _clean, _int_in, run_query

_CAPTURE_DIR = "📥 000-Inbox/Dump"
_OPERATIONS_DIR = "memory-capture-note-operations"
_OP_ID_RE = re.compile(r"^[A-Za-z0-9_-]{8,64}$")
_MAX_CONTENT = 20_000
_MAX_READ_CHARS = 120_000
_KEEP_OPERATIONS = 300


def _vault_id(data_root: Path) -> str:
    active = _active_vault_id(Path(data_root))
    if not active:
        raise MemoryOpError("NO_VAULT", "No vault is registered.", "Register a vault in the Brain product first.")
    return active


def search(data_root: Path, payload: Any) -> dict[str, Any]:
    """The user's own note search (FTS, or hybrid with local semantic search when it is ready)."""
    if not isinstance(payload, dict) or set(payload) - {"query", "limit", "category", "mode"}:
        raise _bad("paths and identities are not accepted", "Send only query, limit, category, mode.")
    query = payload.get("query")
    if not isinstance(query, str) or not 1 <= len(query.strip()) <= 200 or not re.findall(r"\w+", query):
        raise _bad("Invalid query.", "Use 1-200 characters with at least one word.")
    limit = _int_in(payload, "limit", 15, 1, 30)
    category = payload.get("category")
    if category is not None and (not isinstance(category, str) or not 1 <= len(category) <= 64 or "/" in category or "\\" in category):
        raise _bad("Invalid category.", "Use 1-64 characters without path separators.")
    mode = payload.get("mode", "auto")
    if mode not in ("auto", "fts", "semantic", "hybrid"):
        raise _bad("Invalid mode.", "Use auto, fts, semantic or hybrid.")
    return run_query(Path(data_root), _vault_id(data_root), query.strip(), limit, 240, category, mode)


def read(data_root: Path, payload: Any) -> dict[str, Any]:
    """Read one note of the active vault (bounded)."""
    if not isinstance(payload, dict) or set(payload) != {"path"}:
        raise _bad("Invalid payload.", "Send {path} relative to the vault.")
    _vault_id(data_root)
    _, ctx = _context(Path(data_root), {})
    vault = ctx.paths.vault_root
    target = note_path(vault, payload["path"])
    if target is None:
        raise MemoryOpError("BAD_REQUEST", "That is not a readable note path.", "Use a .md path inside the vault.")
    if not target.is_file():
        raise MemoryOpError("NOT_FOUND", "The note does not exist.", "")
    try:
        content = read_note(vault, target.relative_to(vault).as_posix())
    except (OSError, ValueError):
        raise MemoryOpError("NOTE_UNAVAILABLE", "The note cannot be read.", "It may be too large or unsafe.") from None
    stat = target.stat()
    return {"path": target.relative_to(vault).as_posix(), "title": target.stem, "content": content[:_MAX_READ_CHARS], "truncated": len(content) > _MAX_READ_CHARS,
            "size": stat.st_size, "modified": dt.datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds")}


def capture(data_root: Path, operation_id: Any, payload: Any) -> dict[str, Any]:
    """Quick capture: one new note in the vault's Dump inbox; never overwrites; idempotent per operation id."""
    if not isinstance(operation_id, str) or not _OP_ID_RE.match(operation_id):
        raise _bad("Invalid operation id.", "Use 8 to 64 characters from A-Z, a-z, 0-9, _ and -.")
    if not isinstance(payload, dict) or set(payload) - {"title", "content", "tags"}:
        raise _bad("paths and identities are not accepted", "Send only title, content, tags.")
    content, title, tags = payload.get("content"), payload.get("title", ""), payload.get("tags", ["quick-capture"])
    if not isinstance(content, str) or not content.strip() or len(content) > _MAX_CONTENT:
        raise _bad("Invalid content.", f"Use 1-{_MAX_CONTENT} characters.")
    if not isinstance(title, str) or len(_clean(title)) > 120:
        raise _bad("Invalid title.", "Use at most 120 characters.")
    if not isinstance(tags, list) or len(tags) > 8 or not all(isinstance(t, str) and re.fullmatch(r"[\w-]{1,32}", t) for t in tags):
        raise _bad("Invalid tags.", "Use up to 8 tags of 1-32 letters, digits, '_' or '-'.")
    data_root = Path(data_root)
    _vault_id(data_root)
    title = _clean(title) or "Hızlı Not"
    content = content.replace("\r\n", "\n").replace("\x00", "").strip()
    digest = hashlib.sha256(json.dumps([title, content, tags], ensure_ascii=False).encode("utf-8")).hexdigest()
    record_path = data_root / _OPERATIONS_DIR / f"{operation_id}.json"
    try:
        record = json.loads(record_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        record = None
    if isinstance(record, dict) and isinstance(record.get("result"), dict):
        if record.get("payload_sha256") != digest:
            raise MemoryOpError("OPERATION_ID_CONFLICT", "Operation id was used with a different note.", "Use a new operation id.")
        return {**record["result"], "replayed": True}
    _, ctx = _context(data_root, {})
    now = dt.datetime.now()
    slug = re.sub(r"[-\s]+", "-", re.sub(r"[^\w\s-]", "", title.lower())).strip("-")[:40] or "note"
    filename = f"{now:%Y%m%d_%H%M%S}_{slug}.md"
    front = ["---", f"title: {json.dumps(title, ensure_ascii=False)}", f'created: "{now:%Y-%m-%d %H:%M:%S}"', "type: capture", 'category: "Dump"',
             "status: inbox", "source: hub_quick_capture", "tags:", *(["  - " + json.dumps(t, ensure_ascii=False) for t in tags] or ["  []"]), "---", ""]
    body = "\n".join(front) + f"\n# {title}\n\n{content}\n"
    try:
        with writer_lease(ctx):
            target = create_note(ctx.paths.vault_root, ctx.paths.vault_root / _CAPTURE_DIR, filename, body)
    except BusyError:
        raise MemoryOpError("INDEX_BUSY", "Another Brain writer is running.", "Try again shortly.") from None
    except (OSError, ValueError):
        raise MemoryOpError("NOTE_UNAVAILABLE", "The note could not be saved.", "Check that the vault folder is writable.") from None
    result = {"path": target.relative_to(ctx.paths.vault_root).as_posix(), "replayed": False, "indexed": False}
    atomic_write_json(record_path, {"payload_sha256": digest, "created_ns": time.time_ns(), "result": result})
    for old in sorted(record_path.parent.glob("*.json"), key=lambda p: p.stat().st_mtime)[:-_KEEP_OPERATIONS]:
        old.unlink(missing_ok=True)
    try:  # searchable right away; if it fails the next hook/schedule refresh does it
        from ..search.freshness import refresh_now
        result["indexed"] = bool(refresh_now(ctx, attempts=1).get("refreshed"))
    except Exception:
        pass
    return result


def briefing(data_root: Path, payload: Any) -> dict[str, Any]:
    """Generate today's briefing now if it is due (the scheduled task does the same daily)."""
    if not isinstance(payload, dict) or set(payload) != {"confirm"} or payload["confirm"] is not True:
        raise _bad("explicit confirmation required", "Send {confirm: true}.")
    _vault_id(data_root)
    from ..briefing.service import run_if_due
    from ..providers.runner import ModelRunner
    _, ctx = _context(Path(data_root), {})
    status = run_if_due(ctx, model=ModelRunner(ctx), now=dt.datetime.now().astimezone())
    return {"status": status}
