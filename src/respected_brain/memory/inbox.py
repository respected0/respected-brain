"""Protocol-neutral inbox notes: create a new note in one fixed inbox folder of the active vault, or revert it.

Used by the RPP `memory.write` ops (grant-authorized) and by the MCP server (user setting `mcp_write`); neither
protocol owns this logic. Notes never overwrite anything, carry ownership front matter and are revertible until edited.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..core.config import atomic_write_json
from ..core.coordination import writer_lease
from ..core.errors import BusyError
from ..core.platform import path_within_vault

_OPERATIONS_DIR = "memory-write-operations"
_OP_ID_RE = re.compile(r"^[A-Za-z0-9_-]{8,64}$")
_CONTROL_RE = re.compile(r"[\x00-\x1f\x7f-\x9f]")
_MAX_NOTES = 500
_KEEP_OPERATIONS = 500
MCP_INBOX = "🔮 850-Companion/Inbox/MCP"
MCP_GRANT = "mcp"


class MemoryOpError(Exception):
    """Memory operation failure carrying a stable code, a message and a hint."""

    def __init__(self, code: str, message: str, hint: str = "") -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.hint = hint


def clean_text(text: Any, limit: int | None = None, *, ellipsis: bool = False) -> str:
    text = _CONTROL_RE.sub(" ", str(text or "")).replace(">>>", "").replace("<<<", "")
    text = " ".join(text.split())
    if limit is not None and len(text) > limit:
        text = text[:limit] + ("..." if ellipsis else "")
    return text


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None

def _slug(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", title.casefold()).strip("-")[:40] or "note"

def check_op_id(operation_id: Any) -> str:
    if not isinstance(operation_id, str) or not _OP_ID_RE.match(operation_id):
        raise MemoryOpError("BAD_REQUEST", "Invalid operation id.", "Use 8 to 64 characters from A-Z, a-z, 0-9, _ and -.")
    return operation_id

def create_note(open_context, data_root: Path, operation_id: str, *, grant_id: str, source: str, inbox_rel: str, title: str, body: str,
            tags: list, extra_front: list | None = None) -> dict[str, Any]:
    """Create one new inbox note (never overwrites), idempotent per operation id, with a revert record."""
    title = clean_text(title)
    body = body.replace("\r\n", "\n").replace("\x00", "").strip() + "\n"
    digest = hashlib.sha256(json.dumps({"title": title, "body": body, "tags": tags, "grant": grant_id, "extra": extra_front or []},
                                       sort_keys=True).encode("utf-8")).hexdigest()
    record_path = data_root / _OPERATIONS_DIR / f"{operation_id}.json"
    record = _read_json(record_path)
    if isinstance(record, dict) and isinstance(record.get("result"), dict):
        if record.get("payload_sha256") != digest:
            raise MemoryOpError("OPERATION_ID_CONFLICT", "Operation id was used with a different payload.", "Use a new operation id.")
        return {**record["result"], "replayed": True}
    ctx = open_context()
    inbox = ctx.paths.vault_root / inbox_rel
    if not path_within_vault(inbox, ctx.paths.vault_root):
        raise MemoryOpError("UNSAFE_PATH", "The memory inbox is not a normal folder.", "Remove the link at the inbox location.")
    created = datetime.now(timezone.utc)
    name = f"{created:%Y-%m-%d}-{_slug(title)}-{operation_id[:8]}.md"
    target = inbox / name
    front = ["---", f"title: {json.dumps(title, ensure_ascii=False)}", f"source: {source}",
             f"grant: {grant_id}", f"operation_id: {operation_id}", f"created: {created.isoformat()}", *(extra_front or [])]
    if tags:
        front.append("tags: [" + ", ".join(tags) + "]")
    content = "\n".join([*front, "---", "", f"# {title}", "", body])
    try:
        with writer_lease(ctx):
            inbox.mkdir(parents=True, exist_ok=True)
            if sum(1 for _ in inbox.glob("*.md")) >= _MAX_NOTES:
                raise MemoryOpError("INBOX_FULL", "The memory inbox is full.", "Review or remove notes in the inbox first.")
            if target.exists():
                raise MemoryOpError("OPERATION_ID_CONFLICT", "That note already exists.", "Use a new operation id.")
            descriptor, temporary = tempfile.mkstemp(prefix=".", suffix=".tmp", dir=inbox)
            try:
                with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
                    handle.write(content)
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(temporary, target)
            finally:
                Path(temporary).unlink(missing_ok=True)
    except BusyError:
        raise MemoryOpError("INDEX_BUSY", "Another Brain writer is running.", "Try again shortly.") from None
    result = {"path": f"{inbox_rel}/{name}", "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
              "grant_id": grant_id, "created_at": created.isoformat(), "replayed": False, "indexed": False}
    atomic_write_json(record_path, {"payload_sha256": digest, "created_ns": time.time_ns(), "result": result})
    for old in sorted(record_path.parent.glob("*.json"), key=lambda p: (_read_json(p) or {}).get("created_ns", 0))[:-_KEEP_OPERATIONS]:
        old.unlink(missing_ok=True)
    try:  # make the note recallable now; failure only means the next hook/schedule refresh will do it
        from ..search.freshness import refresh_now
        result["indexed"] = bool(refresh_now(ctx, attempts=1).get("refreshed"))
    except Exception:
        pass
    return result

def revert_note(open_context, data_root: Path, operation_id: str, grant_id: str) -> dict[str, Any]:
    record = _read_json(data_root / _OPERATIONS_DIR / f"{operation_id}.json")
    result = record.get("result") if isinstance(record, dict) else None
    if not isinstance(result, dict) or result.get("grant_id") != grant_id:
        raise MemoryOpError("OPERATION_NOT_FOUND", "No such write for this grant.", "Use the operation id of a note this grant wrote.")
    ctx = open_context()
    target = ctx.paths.vault_root / result["path"]
    if not path_within_vault(target, ctx.paths.vault_root):
        raise MemoryOpError("UNSAFE_PATH", "The note path is not safe.", "")
    if not target.is_file():
        return {"operation_id": operation_id, "reverted": True, "already_gone": True}
    if hashlib.sha256(target.read_bytes()).hexdigest() != result["sha256"]:
        raise MemoryOpError("NOTE_CHANGED", "The note was edited after it was written.", "Delete or keep it manually.")
    try:
        with writer_lease(ctx):
            target.unlink()
    except BusyError:
        raise MemoryOpError("INDEX_BUSY", "Another Brain writer is running.", "Try again shortly.") from None
    return {"operation_id": operation_id, "reverted": True, "already_gone": False}


def write_mcp(ctx, operation_id: str, title: str, body: str, tags: list, extra_front: list) -> dict[str, Any]:
    """Note saved by an AI client through the MCP server (only when the user enabled `mcp_write`): inbox only, revertible."""
    check_op_id(operation_id)
    return create_note(lambda: ctx, Path(ctx.paths.data_root), operation_id, grant_id=MCP_GRANT, source="mcp", inbox_rel=MCP_INBOX,
                       title=title, body=body, tags=tags, extra_front=extra_front)


def revert_mcp(ctx, operation_id: str) -> dict[str, Any]:
    return revert_note(lambda: ctx, Path(ctx.paths.data_root), check_op_id(operation_id), MCP_GRANT)
