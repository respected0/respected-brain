"""Authorized memory writes for other products (RPP `memory.write`, `memory.write.revert`).

A caller needs a grant token created with ``write: true``. The note storage itself lives in ``memory.inbox``;
this module only authorizes the caller and validates the payload. Paths and vault identities are never accepted.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from . import memory_grants as grants
from ..memory.inbox import MemoryOpError, check_op_id, clean_text, create_note, revert_note
from ..hints import hint
from .integrations import _context
from .memory import _active_vault_id, _bad, _from_grant

INBOX = "🔮 850-Companion/Inbox/Orchestrator"
_MAX_BODY = 20_000


def _open_context(data_root: Path):
    return lambda: _context(data_root, {})[1]


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
                            hint("Hub'da yazma izinli hafıza izni oluşturun", "respected-orchestrator memory connect --write") + " ve belirtecini kullanın")
    return row


def write(data_root: Path, operation_id: Any, payload: Any) -> dict[str, Any]:
    """Create one new note in the inbox; idempotent per operation id."""
    check_op_id(operation_id)
    if not isinstance(payload, dict) or set(payload) - {"token", "title", "body", "tags"}:
        raise _bad("paths and identities are not accepted", "Send only token, title, body, tags.")
    data_root = Path(data_root)
    row = _authorize(data_root, payload.get("token"))
    title, body, tags = payload.get("title"), payload.get("body"), payload.get("tags", [])
    if not isinstance(title, str) or not 1 <= len(clean_text(title)) <= 120:
        raise _bad("Invalid title.", "Use 1-120 characters.")
    if not isinstance(body, str) or not body.strip() or len(body) > _MAX_BODY:
        raise _bad("Invalid body.", f"Use 1-{_MAX_BODY} characters.")
    if (not isinstance(tags, list) or len(tags) > 8
            or not all(isinstance(t, str) and re.fullmatch(r"[\w-]{1,32}", t) for t in tags)):
        raise _bad("Invalid tags.", "Use up to 8 tags of 1-32 letters, digits, '_' or '-'.")
    return create_note(_open_context(data_root), data_root, operation_id, grant_id=row["grant_id"], source="orchestrator", inbox_rel=INBOX,
                   title=title, body=body, tags=tags)


def revert(data_root: Path, payload: Any) -> dict[str, Any]:
    """Remove a note this grant created, unless it was edited since."""
    if not isinstance(payload, dict) or set(payload) != {"token", "operation_id"}:
        raise _bad("Invalid revert payload.", "Send {token, operation_id}.")
    data_root = Path(data_root)
    row = _authorize(data_root, payload["token"])
    return revert_note(_open_context(data_root), data_root, check_op_id(payload["operation_id"]), row["grant_id"])
