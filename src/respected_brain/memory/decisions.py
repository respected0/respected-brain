"""Decision lifecycle derived from the append-only event log.

Decision lines may carry explicit markers:
  [key: web-framework] [supersedes: web-framework] [valid_from: 2026-11-01] [valid_until: 2026-12-01]
History is never rewritten; the projection only labels records.
"""

from __future__ import annotations

import datetime as dt
import re
from typing import Any, Iterable

STATUSES = {"active", "superseded", "disputed"}

_MARKER = re.compile(
    r"\[(key|subject|konu|supersedes|yerine|valid_from|valid_until)\s*:\s*([^\]]*)\]",
    re.IGNORECASE,
)
_KEY_ALIASES = {"key": "subject", "subject": "subject", "konu": "subject",
                "supersedes": "supersedes", "yerine": "supersedes",
                "valid_from": "valid_from", "valid_until": "valid_until"}


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip().casefold().rstrip(".")


def _date(value: str) -> str:
    value = str(value or "").strip()
    if not value:
        return ""
    try:
        return dt.date.fromisoformat(value[:10]).isoformat()
    except ValueError:
        return value


def parse_decision(text: str) -> dict[str, Any] | None:
    """Split a decision line into its text and explicit lifecycle markers."""
    raw = str(text or "").strip()
    if not raw:
        return None
    fields: dict[str, str] = {}
    supersedes: list[str] = []
    for match in _MARKER.finditer(raw):
        key = _KEY_ALIASES[match.group(1).lower()]
        value = match.group(2).strip()
        if key == "supersedes":
            supersedes.extend(part.strip() for part in re.split(r"[,;|]", value) if part.strip())
        elif value:
            fields[key] = value
    cleaned = re.sub(r"[ \t]{2,}", " ", _MARKER.sub("", raw)).strip(" \t-:;,")
    if not cleaned:
        return None
    return {
        "text": cleaned,
        "subject": fields.get("subject", ""),
        "supersedes": supersedes,
        "valid_from": _date(fields.get("valid_from", "")),
        "valid_until": _date(fields.get("valid_until", "")),
    }


def _matches(reference: str, record: dict[str, Any]) -> bool:
    wanted = _normalize(reference)
    if not wanted:
        return False
    if wanted == _normalize(record["id"]):
        return True
    if record["subject"] and wanted == _normalize(record["subject"]):
        return True
    body = _normalize(record["text"])
    if wanted == body:
        return True
    return len(wanted) >= 4 and (wanted in body or body in wanted)


def _expired(record: dict[str, Any], today: dt.date) -> bool:
    value = record.get("valid_until") or ""
    if not value:
        return False
    try:
        return dt.date.fromisoformat(value[:10]) < today
    except ValueError:
        return False


def collect(events: Iterable[dict[str, Any]], *, now: dt.datetime | None = None) -> list[dict[str, Any]]:
    """Build lifecycle records from events without modifying the events."""
    current_time = now or dt.datetime.now(dt.timezone.utc)
    today = current_time.date() if isinstance(current_time, dt.datetime) else current_time
    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    for event in events:
        if not isinstance(event, dict):
            continue
        event_id = str(event.get("id", "") or "event")
        recorded = str(event.get("ts", "") or "")
        for index, raw in enumerate(event.get("decisions") or []):
            if not isinstance(raw, str):
                continue
            parsed = parse_decision(raw)
            if parsed is None:
                continue
            record_id = f"{event_id}#{index}"
            if record_id in seen:
                continue
            seen.add(record_id)
            records.append({
                **parsed,
                "id": record_id,
                "status": "active",
                "recorded_at": recorded,
                "valid_from": parsed["valid_from"] or (recorded[:10] if recorded else ""),
                "source_agent": str(event.get("provider", "") or "unknown"),
                "session_id": str(event.get("session_id", "") or ""),
                "event_type": str(event.get("event_type", "") or ""),
                "origin": "user_authored" if event.get("event_type") == "manual_note" else "model_inference",
                "review_status": "pending",
                "superseded_by": [],
                "supersession_reason": "",
                "unresolved_supersedes": [],
                "review_required": False,
                "review_reason": "",
            })

    records.sort(key=lambda record: (record["recorded_at"], record["id"]))
    for record in records:
        if _expired(record, today):
            record["status"] = "superseded"
            record["supersession_reason"] = "validity-expired"

    for position, record in enumerate(records):
        for reference in record["supersedes"]:
            targets = [item for item in records[:position] if item["status"] == "active" and _matches(reference, item)]
            if not targets:
                record["unresolved_supersedes"].append(reference)
                record["review_required"] = True
                record["review_reason"] = record["review_reason"] or "unresolved-supersedes"
            for target in targets:
                target["status"] = "superseded"
                target["superseded_by"].append(record["id"])
                target["supersession_reason"] = "explicit"

    groups: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        if record["status"] == "active" and record["subject"]:
            groups.setdefault(_normalize(record["subject"]), []).append(record)
    for group in groups.values():
        if len({_normalize(item["text"]) for item in group}) < 2:
            continue
        for record in group:
            record["status"] = "disputed"
            record["review_required"] = True
            record["review_reason"] = "conflicting-decisions"
    return records


def current(records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted((item for item in records if item["status"] == "active"),
                  key=lambda item: (item["recorded_at"], item["id"]), reverse=True)


def history(records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(records, key=lambda item: (item["recorded_at"], item["id"]), reverse=True)


def review_items(records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    return [item for item in history(records) if item["review_required"]]


def _line(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def render_markdown(records: Iterable[dict[str, Any]], *, updated: str = "") -> str:
    current_records = current(records)
    everything = history(records)
    review = review_items(everything)

    def block(record: dict[str, Any]) -> str:
        label = record["subject"] or "Genel"
        validity = f"{record['valid_from'] or 'kayıt tarihinden'} → {record['valid_until'] or 'açık'}"
        replaced = ", ".join(record["superseded_by"] or record["supersedes"] or []) or "-"
        return (
            f"### {label} — {record['status']}\n"
            f"- **Karar:** {_line(record['text'])}\n"
            f"- **Kayıt:** {record['recorded_at'] or '-'}\n"
            f"- **Geçerlilik:** {validity}\n"
            f"- **Kaynak:** {record['source_agent']} / {record['session_id'] or '-'} / "
            f"{record['origin']} / {record['review_status']}\n"
            f"- **Yerine geçme:** {replaced}\n"
        )

    active_text = "\n".join(block(item) for item in current_records) or "Aktif karar yok."
    history_text = "\n".join(block(item) for item in everything if item["status"] != "active") or "Geçmiş karar yok."
    review_text = "\n".join(
        f"- **{_line(item['text'])}** (`{item['id']}`, {item['status']}, {item['review_reason']})"
        for item in review
    ) or "İnsan incelemesi bekleyen karar yok."
    return (
        "---\n"
        "title: Kararlar\n"
        f"updated: {updated}\n"
        "type: memory\n"
        "tags: [companion, decisions]\n"
        "---\n\n"
        "# Kararlar\n\n"
        "## Güncel\n"
        f"{active_text}\n\n"
        "## Geçmiş / Yerine Geçilen\n"
        f"{history_text}\n\n"
        "## İnsan İncelemesi Gerekli\n"
        f"{review_text}\n"
    )
