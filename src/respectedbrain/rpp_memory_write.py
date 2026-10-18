"""Authorized memory writes for other products (RPP 1.1 `memory.write`, `memory.write.revert`).

A caller needs a grant token created with ``write: true``. Notes are only ever created as new files inside one
fixed inbox folder of the active vault, never overwrite anything, carry ownership front matter, and can be
reverted while the user has not edited them. Paths and vault identities are never accepted from the caller.
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

from . import rpp_memory_grants as grants
from .core.config import atomic_write_json
from .core.coordination import writer_lease
from .core.errors import BusyError
from .core.platform import path_within_vault
from .rpp_integrations import _context
from .rpp_memory import MemoryOpError, _active_vault_id, _bad, _clean, _from_grant

INBOX = "🔮 850-Companion/Inbox/Orchestrator"
_OPERATIONS_DIR = "memory-write-operations"
_OP_ID_RE = re.compile(r"^[A-Za-z0-9_-]{8,64}$")
_MAX_BODY = 20_000
_MAX_NOTES = 500
_KEEP_OPERATIONS = 500


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _authorize(data_root: Path, token: Any) -> dict[str, Any]:
    if not isinstance(token, str) or not token:
        raise _bad("token is required.")
    try:
        row = grants.verify(data_root, token)
    except grants.GrantError as exc:
        raise _from_grant(exc) from None
    active = _active_vault_id(data_root)
    if not active or row.get("vault_id") != active or row.get("write") is not True:
        raise MemoryOpError("PERMISSION_DENIED", "Memory access is not authorized.",
                            "Create a memory grant with write access in the Hub and use its token.")
    return row


def _slug(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", title.casefold()).strip("-")[:40] or "note"


def _check_op_id(operation_id: Any) -> str:
    if not isinstance(operation_id, str) or not _OP_ID_RE.match(operation_id):
        raise _bad("Invalid operation id.", "Use 8 to 64 characters from A-Z, a-z, 0-9, _ and -.")
    return operation_id


def write(data_root: Path, operation_id: Any, payload: Any) -> dict[str, Any]:
    """Create one new note in the inbox; idempotent per operation id."""
    _check_op_id(operation_id)
    if not isinstance(payload, dict) or set(payload) - {"token", "title", "body", "tags"}:
        raise _bad("paths and identities are not accepted", "Send only token, title, body, tags.")
    data_root = Path(data_root)
    row = _authorize(data_root, payload.get("token"))
    title, body, tags = payload.get("title"), payload.get("body"), payload.get("tags", [])
    if not isinstance(title, str) or not 1 <= len(_clean(title)) <= 120:
        raise _bad("Invalid title.", "Use 1-120 characters.")
    if not isinstance(body, str) or not body.strip() or len(body) > _MAX_BODY:
        raise _bad("Invalid body.", f"Use 1-{_MAX_BODY} characters.")
    if (not isinstance(tags, list) or len(tags) > 8
            or not all(isinstance(t, str) and re.fullmatch(r"[\w-]{1,32}", t) for t in tags)):
        raise _bad("Invalid tags.", "Use up to 8 tags of 1-32 letters, digits, '_' or '-'.")
    return _create(None, data_root, operation_id, grant_id=row["grant_id"], source="orchestrator", inbox_rel=INBOX,
                   title=title, body=body, tags=tags)


def _create(ctx, data_root: Path, operation_id: str, *, grant_id: str, source: str, inbox_rel: str, title: str, body: str,
            tags: list, extra_front: list | None = None) -> dict[str, Any]:
    """Create one new inbox note (never overwrites), idempotent per operation id, with a revert record."""
    title = _clean(title)
    body = body.replace("\r\n", "\n").replace("\x00", "").strip() + "\n"
    digest = hashlib.sha256(json.dumps({"title": title, "body": body, "tags": tags, "grant": grant_id, "extra": extra_front or []},
                                       sort_keys=True).encode("utf-8")).hexdigest()
    record_path = data_root / _OPERATIONS_DIR / f"{operation_id}.json"
    record = _read_json(record_path)
    if isinstance(record, dict) and isinstance(record.get("result"), dict):
        if record.get("payload_sha256") != digest:
            raise MemoryOpError("OPERATION_ID_CONFLICT", "Operation id was used with a different payload.", "Use a new operation id.")
        return {**record["result"], "replayed": True}
    if ctx is None:
        _, ctx = _context(data_root, {})
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
        raise MemoryOpError("INDEX_BUSY", "Another SecondBrain writer is running.", "Try again shortly.") from None
    result = {"path": f"{inbox_rel}/{name}", "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
              "grant_id": grant_id, "created_at": created.isoformat(), "replayed": False, "indexed": False}
    atomic_write_json(record_path, {"payload_sha256": digest, "created_ns": time.time_ns(), "result": result})
    for old in sorted(record_path.parent.glob("*.json"), key=lambda p: (_read_json(p) or {}).get("created_ns", 0))[:-_KEEP_OPERATIONS]:
        old.unlink(missing_ok=True)
    try:  # make the note recallable now; failure only means the next hook/schedule refresh will do it
        from .search.freshness import refresh_now
        result["indexed"] = bool(refresh_now(ctx, attempts=1).get("refreshed"))
    except Exception:
        pass
    return result


MCP_INBOX = "🔮 850-Companion/Inbox/MCP"
MCP_GRANT = "mcp"


def write_mcp(ctx, operation_id: str, title: str, body: str, tags: list, extra_front: list) -> dict[str, Any]:
    """Note saved by an AI client through the MCP server (only when the user enabled `mcp_write`): inbox only, revertible."""
    _check_op_id(operation_id)
    return _create(ctx, Path(ctx.paths.data_root), operation_id, grant_id=MCP_GRANT, source="mcp", inbox_rel=MCP_INBOX,
                   title=title, body=body, tags=tags, extra_front=extra_front)


def revert_mcp(ctx, operation_id: str) -> dict[str, Any]:
    return _revert(ctx, Path(ctx.paths.data_root), _check_op_id(operation_id), MCP_GRANT)


def revert(data_root: Path, payload: Any) -> dict[str, Any]:
    """Remove a note this grant created, unless it was edited since."""
    if not isinstance(payload, dict) or set(payload) != {"token", "operation_id"}:
        raise _bad("Invalid revert payload.", "Send {token, operation_id}.")
    data_root = Path(data_root)
    row = _authorize(data_root, payload["token"])
    return _revert(None, data_root, _check_op_id(payload["operation_id"]), row["grant_id"])


def _revert(ctx, data_root: Path, operation_id: str, grant_id: str) -> dict[str, Any]:
    record = _read_json(data_root / _OPERATIONS_DIR / f"{operation_id}.json")
    result = record.get("result") if isinstance(record, dict) else None
    if not isinstance(result, dict) or result.get("grant_id") != grant_id:
        raise MemoryOpError("OPERATION_NOT_FOUND", "No such write for this grant.", "Use the operation id of a note this grant wrote.")
    if ctx is None:
        _, ctx = _context(data_root, {})
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
        raise MemoryOpError("INDEX_BUSY", "Another SecondBrain writer is running.", "Try again shortly.") from None
    return {"operation_id": operation_id, "reverted": True, "already_gone": False}
