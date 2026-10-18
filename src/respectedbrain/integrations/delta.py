"""Minimal, entry-level description of what Respected changed in an AI client's config file.

Why: the ownership manifest used to keep complete before/after copies of files such as ``~/.claude.json`` (which can hold other
MCP servers' environment secrets) for as long as the install exists - and after an uninstall that keeps data. A delta keeps only
the entries Respected added, removed or changed, plus SHA-256 fingerprints of the full files, and can undo exactly those
entries inside whatever the file looks like later (the client rewrites it all the time).

Formats (both are JSON, stored base64 in the manifest):
* ``json``: partial trees. For objects only the keys that differ appear (recursively); for lists only the items that were added
  (``after``) and removed (``before``).
* ``text`` (TOML, Markdown blocks, anything else): line operations - the lines that were inserted, replaced or removed. Removed
  and inserted lines are located by their exact content; a pure removal also records the SHA-256 of the line before it.
"""
from __future__ import annotations

import difflib
import hashlib
import json
from typing import Any

_ABSENT = object()


class DeltaConflict(ValueError):
    """The user (or something else) changed the same entry Respected owns, so it cannot be undone safely."""


def sha256(data: bytes | None) -> str | None:
    return None if data is None else hashlib.sha256(data).hexdigest()


# ---- JSON ---------------------------------------------------------------------------------------------------------------
def _diff(before: Any, after: Any) -> tuple[Any, Any]:
    """(partial before, partial after) for two values that differ; _ABSENT where a side has nothing to contribute."""
    if isinstance(before, dict) and isinstance(after, dict):
        pb: dict = {}
        pa: dict = {}
        for key in {*before, *after}:
            b, a = before.get(key, _ABSENT), after.get(key, _ABSENT)
            if b is not _ABSENT and a is not _ABSENT and b == a:
                continue
            if b is not _ABSENT and a is not _ABSENT and type(b) is type(a) and isinstance(b, (dict, list)):
                sub_b, sub_a = _diff(b, a)
                if sub_b is not _ABSENT:
                    pb[key] = sub_b
                if sub_a is not _ABSENT:
                    pa[key] = sub_a
                continue
            if b is not _ABSENT:
                pb[key] = b
            if a is not _ABSENT:
                pa[key] = a
        return pb, pa
    if isinstance(before, list) and isinstance(after, list):
        return [x for x in before if x not in after], [x for x in after if x not in before]
    return before, after


def _revert_value(before: Any, after: Any, current: Any) -> Any:
    """Undo (before -> after) inside `current`, touching only the entries that differ; DeltaConflict if the same entry changed."""
    if current == after:
        return before
    if current == before:
        return current
    if isinstance(after, dict) and isinstance(current, dict) and isinstance(before, dict):
        result = dict(current)
        for key in {*before, *after}:
            b, a = before.get(key, _ABSENT), after.get(key, _ABSENT)
            c = current.get(key, _ABSENT)
            if a is _ABSENT:                      # we removed it: bring it back only if it is still gone
                if c is _ABSENT:
                    result[key] = b
                continue
            if c is _ABSENT:                      # we added/changed it and it is already gone
                continue
            if b is _ABSENT:                      # we added it
                if c == a:
                    result.pop(key, None)
                elif isinstance(a, (dict, list)) and type(a) is type(c):
                    inner = _revert_value(type(a)(), a, c)
                    if inner == type(a)():
                        result.pop(key, None)
                    else:
                        result[key] = inner
                else:
                    raise DeltaConflict(key)
                continue
            result[key] = _revert_value(b, a, c)
        return result
    if isinstance(after, list) and isinstance(current, list) and isinstance(before, list):
        added = [item for item in after if item not in before]
        removed = [item for item in before if item not in after]
        kept = [item for item in current if item not in added]
        return [*kept, *[item for item in removed if item not in kept]]
    raise DeltaConflict("value")


# ---- text ---------------------------------------------------------------------------------------------------------------
def _lines(data: bytes | None) -> list[str]:
    return [] if data is None else data.decode("utf-8", errors="surrogateescape").splitlines(keepends=True)


def _line_sha(line: str | None) -> str | None:
    return None if line is None else hashlib.sha256(line.encode("utf-8", errors="surrogateescape")).hexdigest()


def _text_ops(before: bytes | None, after: bytes | None) -> list[dict]:
    b, a = _lines(before), _lines(after)
    ops = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, b, a, autojunk=False).get_opcodes():
        if tag == "equal":
            continue
        ops.append({"before": b[i1:i2], "after": a[j1:j2], "prev_sha": _line_sha(b[i1 - 1]) if i1 > 0 else None})
    return ops


def _find(lines: list[str], chunk: list[str]) -> int:
    for start in range(len(lines) - len(chunk) + 1):
        if lines[start:start + len(chunk)] == chunk:
            return start
    return -1


def _revert_text(current: bytes, ops: list[dict], created_by_us: bool) -> bytes:
    lines = _lines(current)
    for op in reversed(ops):
        added, removed = op["after"], op["before"]
        if added:
            at = _find(lines, added)
            if at < 0:
                # A block we inserted into a file that existed: if none of its lines is left the user removed it - nothing to
                # undo. Lines we replaced, a whole file we created, or a partly edited block: someone else's content - conflict.
                if removed or created_by_us or any(line.strip() and line in lines for line in added):
                    raise DeltaConflict("text")
                continue
            lines[at:at + len(added)] = removed
        else:                                   # we removed lines: put them back after the line that preceded them, if still there
            if _find(lines, removed) >= 0:
                continue
            anchor = op.get("prev_sha")
            positions = [i for i, line in enumerate(lines) if _line_sha(line) == anchor] if anchor else [-1]
            if not positions:
                raise DeltaConflict("text-anchor")
            lines[positions[-1] + 1:positions[-1] + 1] = removed
    return "".join(lines).encode("utf-8", errors="surrogateescape")


# ---- public -------------------------------------------------------------------------------------------------------------
def make_delta(before: bytes | None, after: bytes | None) -> bytes:
    """Compact JSON (bytes) with only what differs between two versions of a config file."""
    document: dict[str, Any] = {"v": 1, "before_absent": before is None, "after_absent": after is None}
    try:
        parsed = [json.loads(item.decode("utf-8-sig")) if item is not None else {} for item in (before, after)]
        if not all(isinstance(item, dict) for item in parsed):
            raise ValueError("not an object")
        pb, pa = _diff(parsed[0], parsed[1])
        document.update(fmt="json", before=pb, after=pa)
    except (ValueError, UnicodeDecodeError):
        document.update(fmt="text", ops=_text_ops(before, after))
    return json.dumps(document, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def revert(current: bytes | None, delta: bytes) -> bytes | None:
    """`current` with only Respected's entries undone (None = the file did not exist before Respected and is now empty).

    Raises DeltaConflict when the same entry was changed by someone else."""
    document = json.loads(delta.decode("utf-8"))
    if document["fmt"] == "json":
        if current is None:
            return None
        try:
            parsed = json.loads(current.decode("utf-8-sig"))
        except (ValueError, UnicodeDecodeError):
            raise DeltaConflict("current is not JSON") from None
        if not isinstance(parsed, dict):
            raise DeltaConflict("current is not an object")
        result = _revert_value(document["before"], document["after"], parsed)
        if result == parsed:
            return current                      # nothing of ours left: do not rewrite (and reformat) the client's file
        if document["before_absent"] and result == {}:
            return None
        return json.dumps(result, ensure_ascii=False, indent=2).encode("utf-8") + bytes([10])
    if current is None:
        return None
    result = _revert_text(current, document["ops"], document["before_absent"])
    if document["before_absent"] and not result.strip():
        return None
    return result
