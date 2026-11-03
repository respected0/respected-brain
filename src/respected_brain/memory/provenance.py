"""Provenance metadata shared by Markdown memory records.

The schema is additive: legacy notes keep their bytes and read as unreviewed/unknown.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Any, Mapping

PROVENANCE_VERSION = 1
PROVENANCE_KEYS = (
    "provenance_version",
    "source_agent",
    "session_id",
    "recorded_at",
    "record_type",
    "review_status",
    "origin",
    "source_ref",
    "source_sha256",
)
REVIEW_STATUSES = {"unreviewed", "pending", "approved", "rejected"}
ORIGINS = {"unknown", "model_inference", "user_authored", "user_approved"}

_FRONTMATTER = re.compile(r"\A\ufeff?---[ \t]*\r?\n(.*?)^---[ \t]*(?:\r?\n|$)", re.MULTILINE | re.DOTALL)
_COMMENT = re.compile(r"<!-- RESPECTED-PROVENANCE: (\{[^\r\n]*?\}) -->")


def source_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def recorded_at(value: datetime | str | None = None) -> str:
    if isinstance(value, str):
        return value
    current = value or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.astimezone()
    return current.isoformat()


def build_provenance(
    *,
    source_agent: str,
    session_id: str = "",
    timestamp: datetime | str | None = None,
    record_type: str = "note",
    review_status: str = "pending",
    origin: str = "model_inference",
    source_ref: str = "",
    sha256: str = "",
) -> dict[str, Any]:
    if review_status not in REVIEW_STATUSES:
        review_status = "pending"
    if origin not in ORIGINS:
        origin = "unknown"
    if origin == "model_inference" and review_status == "approved":
        review_status = "pending"
    return {
        "provenance_version": PROVENANCE_VERSION,
        "source_agent": str(source_agent or "unknown"),
        "session_id": str(session_id or ""),
        "recorded_at": recorded_at(timestamp),
        "record_type": str(record_type or "note"),
        "review_status": review_status,
        "origin": origin,
        "source_ref": str(source_ref or ""),
        "source_sha256": str(sha256 or ""),
    }


def parse_frontmatter(content: str) -> tuple[dict[str, str], str]:
    match = _FRONTMATTER.match(content)
    if not match:
        return {}, content
    fields: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if not line or line[0].isspace() or line.startswith("-") or line.lstrip().startswith("#"):
            continue
        key, separator, value = line.partition(":")
        if separator:
            fields[key.strip().lower()] = value.strip().strip('"').strip("'")
    return fields, content[match.end():]


def read_provenance(content: str | Mapping[str, Any]) -> dict[str, Any]:
    fields = parse_frontmatter(content)[0] if isinstance(content, str) else content
    version = fields.get("provenance_version", "")
    try:
        version_number = int(version)
    except (TypeError, ValueError):
        version_number = 0
    review_status = str(fields.get("review_status", "") or "unreviewed")
    origin = str(fields.get("origin", "") or "unknown")
    return {
        "provenance_version": version_number,
        "source_agent": str(fields.get("source_agent", "") or "unknown"),
        "session_id": str(fields.get("session_id", "") or ""),
        "recorded_at": str(fields.get("recorded_at", "") or ""),
        "record_type": str(fields.get("record_type", "") or "note"),
        "review_status": review_status if review_status in REVIEW_STATUSES else "unreviewed",
        "origin": origin if origin in ORIGINS else "unknown",
        "source_ref": str(fields.get("source_ref", "") or ""),
        "source_sha256": str(fields.get("source_sha256", "") or ""),
        "legacy": version_number == 0,
    }


def render_fields(fields: Mapping[str, Any]) -> list[str]:
    lines = []
    for key in PROVENANCE_KEYS:
        if key not in fields:
            continue
        value = fields[key]
        if key == "provenance_version":
            lines.append(f"{key}: {int(value)}")
        else:
            lines.append(f"{key}: {json.dumps(str(value), ensure_ascii=False)}")
    return lines


def enrich_frontmatter(content: str, fields: Mapping[str, Any]) -> str:
    values = {key: fields[key] for key in PROVENANCE_KEYS if key in fields}
    if not values:
        return content
    match = _FRONTMATTER.match(content)
    if not match:
        if content.lstrip("\ufeff").startswith("---"):
            raise ValueError("frontmatter-unterminated")
        bom = "\ufeff" if content.startswith("\ufeff") else ""
        body = content[len(bom):]
        block = "\n".join(["---", *render_fields(values), "---", ""])
        return bom + block + ("\n" + body.lstrip("\r\n") if body else "")
    kept = []
    for line in match.group(1).splitlines():
        key = line.partition(":")[0].strip().lower() if line and not line[0].isspace() else ""
        if key not in values:
            kept.append(line)
    raw = "\n".join([*kept, *render_fields(values)])
    return content[:match.start(1)] + raw + "\n" + content[match.end(1):]


def migrate_text(
    content: str,
    *,
    source_agent: str,
    record_type: str = "note",
    review_status: str = "unreviewed",
    origin: str = "unknown",
    source_ref: str = "",
) -> str:
    existing = parse_frontmatter(content)[0]
    timestamp = existing.get("created") or existing.get("updated") or ""
    fields = build_provenance(
        source_agent=source_agent,
        timestamp=timestamp,
        record_type=record_type,
        review_status=review_status,
        origin=origin,
        source_ref=source_ref,
        sha256=source_hash(content),
    )
    return enrich_frontmatter(content, fields)


def provenance_comment(fields: Mapping[str, Any]) -> str:
    document = json.dumps(dict(fields), ensure_ascii=True, sort_keys=True)
    document = document.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    return f"<!-- RESPECTED-PROVENANCE: {document} -->"


def session_ids_in_text(text: str) -> list[str]:
    found = []
    for match in _COMMENT.finditer(text):
        try:
            document = json.loads(match.group(1))
        except ValueError:
            continue
        session_id = document.get("session_id") if isinstance(document, dict) else None
        if isinstance(session_id, str) and session_id and session_id not in found:
            found.append(session_id)
    return found