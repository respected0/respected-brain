"""Safe, structured diagnostics for the memory pipeline."""

from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import re
import time
from typing import Any
import uuid

from ..core import platform as runtime_platform
from ..core.config import atomic_write_json


STAGES = frozenset(
    {"capture", "redact", "summarize", "daily_write", "event_project", "compile", "index", "recall"}
)
_REASON = re.compile(r"[a-z][a-z0-9-]{0,63}(?::[A-Za-z0-9][A-Za-z0-9._:-]{0,63})?\Z")
_TOKEN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z")
_PRESERVED = (
    "status", "event", "error", "component", "warnings", "reason", "stage",
    "operation_id", "session_id", "provider",
)


def safe_reason(value: object) -> str:
    """Return a stable code, never free-form text that may contain paths or secrets."""
    text = str(value or "").strip()
    return text if _REASON.fullmatch(text) else "unclassified"


def reason_for(error: BaseException) -> str:
    """Reduce an exception to a safe reason code."""
    code = safe_reason(error)
    if code != "unclassified":
        return code
    return f"error:{_token(type(error).__name__, 'Exception')}"


def _token(value: object, default: str | None) -> str | None:
    text = str(value or "")
    return text if _TOKEN.fullmatch(text) else default


def _load(path: Path) -> dict[str, Any]:
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
        json.dumps(loaded, allow_nan=False)
    except (OSError, ValueError, TypeError):
        return {}
    if not isinstance(loaded, dict):
        return {}
    payload = {key: loaded[key] for key in _PRESERVED if key in loaded}
    warnings = payload.get("warnings")
    if isinstance(warnings, list):
        payload["warnings"] = [
            code for value in warnings
            if (code := safe_reason(value)) != "unclassified"
        ][-20:]
    else:
        payload.pop("warnings", None)
    return payload


def record_health(
    state_dir: Path,
    *,
    stage: str,
    reason: object,
    component: str,
    warning: bool = False,
    operation_id: str | None = None,
    session_id: str | None = None,
    provider: str | None = None,
    event: str | None = None,
    now: datetime | None = None,
    ts: int | None = None,
) -> None:
    """Merge a redacted diagnostic event into health.json without crashing the caller."""
    health_path = state_dir / "health.json"
    if not runtime_platform.path_within_vault(health_path, state_dir):
        return
    payload = _load(health_path)
    code = safe_reason(reason)
    if warning:
        warnings = payload.get("warnings", [])
        if code not in warnings:
            warnings.append(code)
        payload["warnings"] = warnings[-20:]
    else:
        payload["status"] = "degraded"
    payload.update(
        {
            "error": code,
            "reason": code,
            "component": _token(component, "memory") or "memory",
            "stage": stage if stage in STAGES else "capture",
            "operation_id": _token(operation_id, None) or uuid.uuid4().hex,
            "ts": ts if ts is not None else int((now or datetime.now().astimezone()).timestamp()),
        }
    )
    if session_id is not None and (value := _token(session_id, None)):
        payload["session_id"] = value
    if provider is not None and (value := _token(provider, None)):
        payload["provider"] = value
    if event is not None and (value := _token(event, None)):
        payload["event"] = value
    stamp = now or datetime.fromtimestamp(payload["ts"]).astimezone()
    payload["updated_at"] = stamp.isoformat(timespec="seconds")
    try:
        atomic_write_json(health_path, payload)
    except (OSError, ValueError, TypeError):
        pass
