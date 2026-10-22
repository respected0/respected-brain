"""Explicit authorization store for read-only RPP memory recall.

A caller needs a secret token created by the user's Hub; only its SHA-256 is stored.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from respected_brain.core.config import atomic_write_json
from respected_brain.hints import hint
from respected_brain.core.locking import exclusive_lock

GRANTS_FILE = "memory-grants.json"
MAX_ACTIVE = 20
_LOCK_FILE = ".memory-grants.lock"
_ID_RE = re.compile(r"^[A-Za-z0-9_-]{8,64}$")
_LABEL_RE = re.compile(r"^[A-Za-z0-9 ._-]{1,80}$")
_DENIED = "Memory access is not authorized."


class GrantError(Exception):
    """Grant failure carrying a stable code, a message and a hint."""

    def __init__(self, code: str, message: str, hint: str = "") -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.hint = hint


def _denied() -> GrantError:
    return GrantError("PERMISSION_DENIED", _DENIED, hint("Hub'da hafıza izni oluşturun", "respected-orchestrator memory connect") + " ve belirtecini kullanın")


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _load(data_root: Path) -> list[dict[str, Any]]:
    path = Path(data_root) / GRANTS_FILE
    if not path.exists():
        return []
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise GrantError("GRANTS_CORRUPT", "Memory grants file is unreadable.", "Repair or remove it manually.") from exc
    grants = document.get("grants") if isinstance(document, dict) else None
    if not isinstance(grants, list) or not all(
        isinstance(g, dict) and isinstance(g.get("grant_id"), str) and isinstance(g.get("token_sha256"), str)
        for g in grants
    ):
        raise GrantError("GRANTS_CORRUPT", "Memory grants file is malformed.", "Repair or remove it manually.")
    return grants


def _save(data_root: Path, grants: list[dict[str, Any]]) -> None:
    path = Path(data_root) / GRANTS_FILE
    atomic_write_json(path, {"schema_version": 1, "grants": grants})
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def _public(grant: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in grant.items() if k != "token_sha256"}


def create(data_root: Path, grant_id: str, label: str, vault_id: str, max_results: int = 20, write: bool = False) -> dict[str, Any]:
    """Create a grant; the returned token is shown exactly once."""
    if not isinstance(grant_id, str) or not _ID_RE.match(grant_id):
        raise GrantError("BAD_REQUEST", "Invalid grant id.", "Use 8-64 letters, digits, '_' or '-'.")
    if not isinstance(label, str) or not _LABEL_RE.match(label):
        raise GrantError("BAD_REQUEST", "Invalid label.", "Use 1-80 letters, digits, space, '.', '_' or '-'.")
    if not isinstance(vault_id, str) or not vault_id:
        raise GrantError("BAD_REQUEST", "Invalid vault id.", "Provide a non-empty vault id.")
    if isinstance(max_results, bool) or not isinstance(max_results, int) or not 1 <= max_results <= 20:
        raise GrantError("BAD_REQUEST", "Invalid max_results.", "Use an integer from 1 to 20.")
    if not isinstance(write, bool):
        raise GrantError("BAD_REQUEST", "Invalid write flag.", "Use true or false.")
    root = Path(data_root)
    with exclusive_lock(root / _LOCK_FILE):
        grants = _load(root)
        if any(g["grant_id"] == grant_id for g in grants):
            raise GrantError("GRANT_EXISTS", "Grant id already used.", "Use a fresh operation id.")
        if sum(1 for g in grants if not g.get("revoked")) >= MAX_ACTIVE:
            raise GrantError("GRANT_LIMIT", "Too many active grants.", "Revoke an unused grant first.")
        token = "rbm_" + secrets.token_urlsafe(32)
        created_at = datetime.now(timezone.utc).isoformat()
        grants.append({
            "grant_id": grant_id,
            "token_sha256": _hash(token),
            "label": label,
            "vault_id": vault_id,
            "max_results": max_results,
            "write": write,
            "created_at": created_at,
            "revoked": False,
        })
        _save(root, grants)
    return {
        "grant_id": grant_id,
        "token": token,
        "label": label,
        "vault_id": vault_id,
        "max_results": max_results,
        "write": write,
        "created_at": created_at,
    }


def verify(data_root: Path, token: str) -> dict[str, Any]:
    """Return the public grant matching the token, or raise PERMISSION_DENIED."""
    if not isinstance(token, str) or not token:
        raise _denied()
    try:
        grants = _load(data_root)
    except GrantError:
        raise _denied() from None
    digest = _hash(token)
    match = None
    for grant in grants:  # scan all grants; never stop at the first match
        if not grant.get("revoked") and hmac.compare_digest(digest, grant["token_sha256"]):
            match = grant
    if match is None:
        raise _denied()
    return _public(match)


def revoke(data_root: Path, grant_id: str) -> dict[str, Any]:
    """Revoke a grant; repeating it is a no-op."""
    root = Path(data_root)
    with exclusive_lock(root / _LOCK_FILE):
        grants = _load(root)
        for grant in grants:
            if grant["grant_id"] == grant_id:
                if not grant.get("revoked"):
                    grant["revoked"] = True
                    _save(root, grants)
                return {"grant_id": grant_id, "revoked": True}
    raise GrantError("GRANT_NOT_FOUND", "Unknown grant id.", "List grants to find the id.")

