"""memory_index: explicit, confirmed refresh of the product's own search index (never writes the vault)."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import re
import time
from typing import Any

from ..core.config import ConfigStore, atomic_write_json
from .integrations import _context
from ..search.engine import IndexUnavailable, SearchEngine
from ..search.freshness import refresh_semantic

_OPERATION_ID_RE = re.compile(r"^[A-Za-z0-9_-]{8,64}$")
_OPERATIONS_DIR = "memory-index-operations"
_REFRESH_FILE = "memory-index-refresh.json"
_KEEP_OPERATIONS = 50


class MemoryIndexError(Exception):
    """Index operation failure carrying a stable code, a message and a hint."""

    def __init__(self, code: str, message: str, hint: str = "") -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.hint = hint


def _bad(message: str, hint: str = "") -> MemoryIndexError:
    return MemoryIndexError("BAD_REQUEST", message, hint)


def _active_vault_id(data_root: Path) -> str:
    vault_id = ConfigStore(Path(data_root)).read().get("active_vault_id")
    if not vault_id:
        raise MemoryIndexError("NO_VAULT", "No vault is registered.", "Register a vault in the Brain product first.")
    return vault_id


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _index_state(ctx) -> dict[str, Any]:
    try:
        return SearchEngine.open_read_only(ctx).index_state()
    except IndexUnavailable as exc:
        state = "missing" if exc.code == "INDEX_MISSING" else "invalid"
    except ValueError:  # unsafe index path
        state = "invalid"
    return {"state": state, "indexed_files": None, "checked_files": None, "changed_files": None}


def status(data_root: Path) -> dict[str, Any]:
    """Report index freshness and the last refresh; writes nothing."""
    data_root = Path(data_root)
    vault_id = _active_vault_id(data_root)
    _, ctx = _context(data_root, {})
    last = _read_json(data_root / _REFRESH_FILE)
    return {"vault_id": vault_id, "index": _index_state(ctx), "last_refresh": last if isinstance(last, dict) else None}


def _validate(operation_id: Any, payload: Any) -> bool:
    if not isinstance(operation_id, str) or not _OPERATION_ID_RE.match(operation_id):
        raise _bad("Invalid operation id.", "Use 8 to 64 characters from A-Z, a-z, 0-9, _ and -.")
    if not isinstance(payload, dict) or set(payload) - {"confirm", "force"}:
        raise _bad("paths and identities are not accepted", "Send {confirm: true, force?: bool}.")
    if payload.get("confirm") is not True:
        raise _bad("explicit confirmation required", "Send {confirm: true}.")
    force = payload.get("force", False)
    if not isinstance(force, bool):
        raise _bad("Invalid force.", "Use a boolean.")
    return force


def _prune(directory: Path) -> None:
    def created(path: Path) -> tuple[int, str]:  # file mtime can tie on coarse clocks
        record = _read_json(path)
        return (record.get("created_ns", 0) if isinstance(record, dict) else 0, path.name)

    records = sorted(directory.glob("*.json"), key=created)
    for old in records[:-_KEEP_OPERATIONS]:
        old.unlink(missing_ok=True)


def refresh(data_root: Path, operation_id: Any, payload: Any) -> dict[str, Any]:
    """Re-index the active vault into the product's own cache; idempotent per operation id."""
    force = _validate(operation_id, payload)
    data_root = Path(data_root)
    vault_id = _active_vault_id(data_root)
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    record_path = data_root / _OPERATIONS_DIR / f"{operation_id}.json"
    if record_path.is_file():
        record = _read_json(record_path)
        if isinstance(record, dict) and isinstance(record.get("result"), dict):
            if record.get("payload_sha256") != digest:
                raise MemoryIndexError("OPERATION_ID_CONFLICT", "Operation id was used with a different payload.",
                                       "Use a new operation id.")
            return {**record["result"], "replayed": True}
    _, ctx = _context(data_root, {})
    started = time.monotonic()
    stats = SearchEngine(ctx).index_vault(force=force)
    if stats is None:
        raise MemoryIndexError("INDEX_BUSY", "The index is being written by another process.",
                               "another Brain writer is running; try again shortly")
    duration = round(time.monotonic() - started, 3)
    result = {
        "vault_id": vault_id, "indexed": stats["indexed"], "skipped": stats["skipped"], "deleted": stats["deleted"],
        "total": stats["total"], "duration_seconds": duration, "force": force, "replayed": False,
        "index": _index_state(ctx), "semantic": refresh_semantic(ctx),
    }
    atomic_write_json(record_path, {"payload_sha256": digest, "created_ns": time.time_ns(), "result": result})
    atomic_write_json(data_root / _REFRESH_FILE, {
        "at": datetime.now(timezone.utc).isoformat(), "operation_id": operation_id, "indexed": stats["indexed"],
        "skipped": stats["skipped"], "deleted": stats["deleted"], "total": stats["total"],
        "duration_seconds": duration, "force": force,
    })
    _prune(record_path.parent)
    return result
