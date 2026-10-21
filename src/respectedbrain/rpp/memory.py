"""Read-only RPP memory recall: grant management plus bounded snippet search.

Recall never writes to the vault or the data root and never accepts a path from the caller.
Hits whose note changed since indexing are dropped (``dropped_stale``) instead of returning old indexed
text, so the effective result may be shorter than ``limit`` until the index is refreshed.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

from . import memory_grants as grants
from ..core.config import ConfigStore
from ..core.platform import path_within_vault
from .integrations import _context
from ..search.engine import IndexUnavailable, SearchEngine

_ALLOWED_KEYS = {"token", "query", "limit", "snippet_chars", "category", "mode"}
_MODES = ("auto", "fts", "semantic", "hybrid")
_CONTROL_RE = re.compile(r"[\x00-\x1f\x7f-\x9f]")
_MAX_HASH_BYTES = 2_000_000
_INDEX_HINT = "recall never builds or repairs the index; refresh it with the SecondBrain product"


class MemoryOpError(Exception):
    """Memory operation failure carrying a stable code, a message and a hint."""

    def __init__(self, code: str, message: str, hint: str = "") -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.hint = hint


def _bad(message: str, hint: str = "") -> MemoryOpError:
    return MemoryOpError("BAD_REQUEST", message, hint)


def _from_grant(exc: grants.GrantError) -> MemoryOpError:
    return MemoryOpError(exc.code, exc.message, exc.hint)


def _int_in(payload: dict[str, Any], key: str, default: int, low: int, high: int) -> int:
    value = payload.get(key, default)
    if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
        raise _bad(f"Invalid {key}.", f"Use an integer from {low} to {high}.")
    return value


def _active_vault_id(data_root: Path) -> str | None:
    return ConfigStore(Path(data_root)).read().get("active_vault_id")


def grant(data_root: Path, operation_id: Any, payload: Any) -> dict[str, Any]:
    """Create a memory grant bound to the active vault; the token is shown once."""
    if not isinstance(operation_id, str) or not operation_id:
        raise _bad("An operation_id is required.", "Send a fresh operation_id; it becomes the grant id.")
    if not isinstance(payload, dict) or set(payload) - {"label", "max_results", "write"} or not isinstance(payload.get("label"), str):
        raise _bad("Invalid grant payload.", "Send {label, max_results?}.")
    vault_id = _active_vault_id(data_root)
    if not vault_id:
        raise MemoryOpError("NO_VAULT", "No vault is registered.", "Register a vault in the SecondBrain product first.")
    try:
        return grants.create(Path(data_root), operation_id, payload["label"], vault_id, payload.get("max_results", 20), payload.get("write", False))
    except grants.GrantError as exc:
        raise _from_grant(exc) from None


def revoke(data_root: Path, payload: Any) -> dict[str, Any]:
    """Revoke a memory grant by id."""
    if not isinstance(payload, dict) or set(payload) != {"grant_id"} or not isinstance(payload["grant_id"], str):
        raise _bad("Invalid revoke payload.", "Send {grant_id}.")
    try:
        return grants.revoke(Path(data_root), payload["grant_id"])
    except grants.GrantError as exc:
        raise _from_grant(exc) from None


def _validate(payload: Any) -> tuple[str, str, int, int, str | None, str]:
    if not isinstance(payload, dict):
        raise _bad("Payload must be an object.")
    if set(payload) - _ALLOWED_KEYS:
        raise _bad("paths and identities are not accepted", "Send only token, query, limit, snippet_chars, category.")
    token, query = payload.get("token"), payload.get("query")
    if not isinstance(token, str) or not token:
        raise _bad("token is required.")
    if not isinstance(query, str):
        raise _bad("query is required.")
    query = query.strip()
    if not 1 <= len(query) <= 200 or not 1 <= len(re.findall(r"\w+", query)) <= 12:
        raise _bad("Invalid query.", "Use 1-200 characters and 1-12 word terms.")
    limit = _int_in(payload, "limit", 5, 1, 20)
    snippet_chars = _int_in(payload, "snippet_chars", 200, 40, 400)
    category = payload.get("category")
    if category is not None and (
        not isinstance(category, str) or not 1 <= len(category) <= 64
        or "/" in category or "\\" in category or ".." in category
    ):
        raise _bad("Invalid category.", "Use 1-64 characters without '/', '\\' or '..'.")
    mode = payload.get("mode", "auto")
    if mode not in _MODES:
        raise _bad("Invalid mode.", "Use auto, fts, semantic or hybrid.")
    return token, query, limit, snippet_chars, category, mode


def _normal_relative(path: Any) -> bool:
    if not isinstance(path, str) or not path or "\\" in path or re.match(r"^[A-Za-z]:", path):
        return False
    return all(part not in ("", "..") for part in path.split("/"))


def _clean(text: Any, limit: int | None = None, *, ellipsis: bool = False) -> str:
    text = _CONTROL_RE.sub(" ", str(text or "")).replace(">>>", "").replace("<<<", "")
    text = " ".join(text.split())
    if limit is not None and len(text) > limit:
        text = text[:limit] + ("..." if ellipsis else "")
    return text


def _matches_index(file: Path, indexed: tuple[float, str] | None) -> bool:
    """True only if the file's current bytes hash to the indexed sha256 (bytes are never returned)."""
    if indexed is None:
        return False
    try:
        with file.open("rb") as handle:
            data = handle.read(_MAX_HASH_BYTES + 1)
    except OSError:
        return False
    return len(data) <= _MAX_HASH_BYTES and hashlib.sha256(data).hexdigest() == indexed[1]


def _lead(file: Path, chars: int) -> str:
    """Opening text of a note (front matter skipped) for hits that only the semantic ranking found."""
    try:
        text = file.read_bytes()[:_MAX_HASH_BYTES].decode("utf-8", "replace")
    except OSError:
        return ""
    if text.startswith("---"):
        parts = text.split("---", 2)
        text = parts[2] if len(parts) == 3 else text
    return " ".join(text.split())[:chars]


def _find(ctx, engine, data_root, query, limit, category, mode, snippet_chars):
    """FTS hits, semantic hits or their reciprocal-rank fusion; semantic problems fall back to FTS (never an error in auto/hybrid)."""
    from ..search import semantic
    cfg = semantic.load_config(data_root)
    want_semantic = mode in ("semantic", "hybrid") or (mode == "auto" and cfg["enabled"])
    info = {"mode": "fts", "semantic": "off" if not cfg["enabled"] else "not_used"}
    if mode in ("semantic", "hybrid") and not cfg["enabled"]:
        raise MemoryOpError("SEMANTIC_OFF", "Semantic search is not enabled.", "Enable it from the Hub, or use mode fts.")
    ranked: list[tuple[str, float]] = []
    if want_semantic and cfg["enabled"]:
        try:
            ranked = semantic.search(ctx, cfg, query, limit * 3)
            info = {"mode": "hybrid" if mode != "semantic" else "semantic", "semantic": "ok", "model": cfg["model"]}
        except semantic.SemanticError as error:
            if mode == "semantic":
                raise MemoryOpError(error.code, error.message, error.hint) from None
            info = {"mode": "fts", "semantic": "unavailable", "reason": error.code}
    fts = engine.search(query, limit=limit, category=category) if info["mode"] != "semantic" else []
    if not ranked:
        return fts, info
    by_path = {hit["path"]: hit for hit in fts}
    score: dict[str, float] = {}
    for position, hit in enumerate(fts):
        score[hit["path"]] = score.get(hit["path"], 0.0) + 1.0 / (60 + position)
    for position, (path, _) in enumerate(ranked):
        score[path] = score.get(path, 0.0) + 1.0 / (60 + position)
    missing = [p for p in score if p not in by_path]
    if missing:
        with engine._get_connection() as con:
            meta = {r["rel_path"]: r for r in con.execute(
                f"SELECT rel_path, title, category FROM files_meta WHERE rel_path IN ({','.join('?' * len(missing))})", missing)}
        for path in missing:
            row = meta.get(path)
            if row is None or (category and row["category"] != category):
                score.pop(path)
                continue
            by_path[path] = {"path": path, "title": row["title"], "category": row["category"], "tags": "",
                             "snippet": _lead(engine.vault_root / path, snippet_chars)}
    order = sorted(score, key=lambda p: -score[p])[:limit]
    return [{**by_path[p], "score": round(score[p], 5)} for p in order], info


def recall(data_root: Path, payload: Any) -> dict[str, Any]:
    """Return bounded snippets for a query; strictly read-only.

    Hits whose file is missing or unsafe are counted in ``dropped``; hits whose current file bytes no
    longer match the indexed sha256 (edited, or over 2,000,000 bytes) are counted in ``dropped_stale``.
    ``count`` is the number of returned results and may be below ``limit``."""
    token, query, limit, snippet_chars, category, mode = _validate(payload)
    try:
        grant_row = grants.verify(Path(data_root), token)
    except grants.GrantError as exc:
        raise _from_grant(exc) from None
    active = _active_vault_id(data_root)
    if not active or grant_row.get("vault_id") != active:
        raise MemoryOpError("PERMISSION_DENIED", "Memory access is not authorized.",
                            "Create a memory grant in the Hub and use its token.")
    effective = min(limit, int(grant_row.get("max_results", 20)))
    result = run_query(data_root, active, query, effective, snippet_chars, category, mode)
    return {**result, "grant_id": grant_row["grant_id"]}


def run_query(data_root: Path, active: str, query: str, limit: int, snippet_chars: int, category: str | None, mode: str) -> dict[str, Any]:
    """The read-only, hash-verified search shared by token-based recall and the user's own Hub search."""
    _, ctx = _context(Path(data_root), {})
    try:
        engine = SearchEngine.open_read_only(ctx)
    except IndexUnavailable as exc:
        raise MemoryOpError(exc.code, "The search index is not available.", _INDEX_HINT) from None
    except ValueError:  # unsafe index path (link or outside the data root)
        raise MemoryOpError("INDEX_INVALID", "The search index is not usable.", _INDEX_HINT) from None
    hits, search_info = _find(ctx, engine, data_root, query, limit, category, mode, snippet_chars)
    vault_root = engine.vault_root
    results: list[dict[str, Any]] = []
    dropped = dropped_stale = 0
    safe: list[dict[str, Any]] = []
    for hit in hits:
        path = hit.get("path")
        if not (_normal_relative(path) and path_within_vault(vault_root / path, vault_root)
                and (vault_root / path).is_file()):
            dropped += 1
            continue
        safe.append(hit)
    fingerprints = engine.indexed_fingerprints([hit["path"] for hit in safe])
    for hit in safe:
        path = hit["path"]
        if not _matches_index(vault_root / path, fingerprints.get(path)):
            dropped_stale += 1
            continue
        results.append({
            "path": path,
            "title": _clean(hit.get("title"), 200),
            "category": _clean(hit.get("category"), 64),
            "tags": _clean(hit.get("tags"), 200),
            "snippet": _clean(hit.get("snippet"), snippet_chars, ellipsis=True),
            "score": hit.get("score"),
        })
    return {
        "results": results, "count": len(results), "dropped": dropped, "dropped_stale": dropped_stale, "limit": limit,
        "read_only": True, "search": search_info, "index": engine.index_state(), "vault_id": active,
    }
