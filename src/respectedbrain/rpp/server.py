"""Respected Product Protocol (RPP) v1.1 private entry point for Respected SecondBrain.

v1.1 is a strict superset of v1.0: existing ops and response shapes are unchanged and
the response echoes the negotiated protocol version. One JSON request on stdin, one JSON
response line on stdout. No network listener, no daemon, no public CLI. The data root can
be overridden explicitly so tests never touch real user data.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from ..core.config import ConfigStore, atomic_write_json, validate_config
from ..core.errors import FoundationError, SelectionError
from . import integrations, lifecycle, memory, memory_grants, memory_capture, memory_index, memory_semantic, memory_workspace, memory_write

PROTOCOL_MIN = "1.0"
PROTOCOL_MAX = "1.1"
RPP_VERSION = PROTOCOL_MIN  # v1.0 name retained for existing importers
PRODUCT_ID = "respected-secondbrain"
SECRET_MASK = "***set***"
_OPERATION_ID = re.compile(r"^[A-Za-z0-9_-]{8,64}$")

# Only features that exist in this checkout, each backed by a real module.
CAPABILITIES = ("briefing", "capture", "hooks_dispatch", "mcp_serve", "recall", "memory_recall", "memory_write", "memory_semantic", "memory_capture", "memory_workspace", "memory_index")

# Per-capability descriptors required by the v1.1 manifest. Each capability is configured
# or inspected through the listed ops.
CAPABILITY_DETAILS = (
    {"id": "briefing", "since": "1.0", "ops": ["settings.readback", "settings.apply"]},
    {"id": "capture", "since": "1.0", "ops": ["settings.apply"]},
    {"id": "hooks_dispatch", "since": "1.0", "ops": ["settings.apply", "settings.readback"]},
    {"id": "mcp_serve", "since": "1.0", "ops": ["health", "settings.readback"]},
    {"id": "recall", "since": "1.0", "ops": ["settings.readback"]},
    {"id": "memory_recall", "since": "1.1", "ops": ["memory.grant", "memory.revoke", "memory.recall"]},
    {"id": "memory_semantic", "since": "1.1", "ops": ["memory.semantic.status", "memory.semantic.configure", "memory.semantic.pull"]},
    {"id": "memory_capture", "since": "1.1", "ops": ["memory.capture.run"]},
    {"id": "memory_workspace", "since": "1.1", "ops": ["memory.search", "memory.note.read", "memory.capture.note", "memory.briefing.run"]},
    {"id": "memory_write", "since": "1.1", "ops": ["memory.write", "memory.write.revert"]},
    {"id": "memory_index", "since": "1.1", "ops": ["memory.index.status", "memory.index.refresh"]},
)

# Allow-listed keys that really exist in resources/defaults.json.
SETTINGS_FIELDS = (
    {"key": "summary_provider", "type": "enum", "label": "Summary provider",
     "default": "auto", "secret": False,
     "enum": ["auto", "codex", "claude", "antigravity", "gemini", "cursor"]},
    {"key": "capture_mode", "type": "enum", "label": "Capture mode", "default": "auto", "secret": False,
     "enum": ["auto", "manual"]},
    {"key": "mcp_write", "type": "boolean", "label": "Allow AI tools to save notes through MCP (inbox only, reviewable)",
     "default": False, "secret": False},
    {"key": "archive_transcripts", "type": "boolean", "label": "Keep redacted session transcripts for compaction recovery",
     "default": False, "secret": False},
    {"key": "transcript_retention_days", "type": "integer", "label": "Days to keep session transcripts", "default": 14,
     "secret": False, "min": 1, "max": 90},
    {"key": "provider_fallback", "type": "boolean", "label": "Provider fallback",
     "default": True, "secret": False},
    {"key": "integrations.global", "type": "boolean", "label": "Global integration",
     "default": False, "secret": False},
    {"key": "integrations.mcp", "type": "boolean", "label": "MCP integration",
     "default": False, "secret": False},
    {"key": "integrations.schedule", "type": "boolean", "label": "Scheduled integration",
     "default": False, "secret": False},
    {"key": "integrations.shortcut", "type": "boolean", "label": "Shortcut integration",
     "default": False, "secret": False},
)
_SCHEMA = {field["key"]: field for field in SETTINGS_FIELDS}

_V10_OPS = ("manifest", "health", "settings.schema", "settings.validate",
            "settings.apply", "settings.readback")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _product_version() -> str:
    try:
        from importlib.metadata import version
        return version("respectedbrain")
    except Exception:
        return "unknown"


def _flat(receipt):  # same result shape as the Orchestrator server
    return {key: receipt.get(key) for key in ("status", "applied_at", "settings_sha256")}


def _reply(version, ok, operation_id, result, error) -> dict:
    return {"rpp": version, "ok": ok, "operation_id": operation_id,
            "result": result if error is None else None, "error": error}


def _error(code, message, hint) -> dict:
    return {"code": code, "message": message, "hint": hint}


def _resolve_data_root(override) -> Path:
    value = override if override is not None else os.environ.get("RESPECTED_RPP_DATA_ROOT")
    if value is not None:
        path = Path(value)
        if not path.is_absolute():
            raise SelectionError("RPP data root must be an absolute path")
        return path.resolve()
    from ..bootstrap import application_roots
    return application_roots().data_root


def _op_manifest(version, operation_id, data_root):
    state = lifecycle.inspect(data_root)
    since = {item["id"]: item["since"] for item in CAPABILITY_DETAILS}
    visible = [cap for cap in CAPABILITIES if version != PROTOCOL_MIN or since.get(cap) != "1.1"]
    result = {
        "product_id": PRODUCT_ID,
        "product_version": _product_version(),
        "protocol": {"min": PROTOCOL_MIN, "max": PROTOCOL_MAX},
        "capabilities": visible,
        "settings_supported": True,
        "installed": state["installed"],
        "install_state": state["install_state"],
        "roots": state["roots"],
        "capability_details": [dict(item) for item in CAPABILITY_DETAILS],
    }
    return _reply(version, True, operation_id, result, None)


def _op_health(version, operation_id, data_root):
    checks = []
    writable = False
    detail = str(data_root)
    try:
        data_root.mkdir(parents=True, exist_ok=True)
        writable = os.access(data_root, os.W_OK)
        if not writable:
            detail = f"Not writable: {data_root}"
    except OSError as error:
        detail = f"Cannot prepare data root: {error}"
    checks.append({"name": "data_root_writable", "ok": writable, "detail": detail})

    document = None
    config_ok = False
    config_detail = "Configuration loaded"
    try:
        document = ConfigStore(data_root).read()
        config_ok = True
    except (SelectionError, OSError, ValueError) as error:
        config_detail = f"Configuration unavailable: {error}"
    checks.append({"name": "config_loads", "ok": config_ok, "detail": config_detail})

    vault_ok = False
    vault_detail = "No active vault configured"
    if document is not None:
        active = document.get("active_vault_id")
        vaults = document.get("vaults") or {}
        if active and active in vaults:
            entry = vaults[active]
            vault_ok = bool(entry)
            vault_detail = f"Vault registered: {entry}"
    checks.append({"name": "vault_registered", "ok": vault_ok, "detail": vault_detail})

    if not writable or not config_ok:
        status = "unhealthy"
    elif all(check["ok"] for check in checks):
        status = "healthy"
    else:
        status = "degraded"
    result = {"status": status, "version": _product_version(), "checks": checks}
    return _reply(version, True, operation_id, result, None)


def _op_schema(version, operation_id):
    fields = []
    for field in SETTINGS_FIELDS:
        item = {"key": field["key"], "type": field["type"], "label": field["label"],
                "default": field["default"], "secret": field["secret"]}
        if "enum" in field:
            item["enum"] = list(field["enum"])
        if "min" in field:
            item["min"] = field["min"]
        if "max" in field:
            item["max"] = field["max"]
        fields.append(item)
    return _reply(version, True, operation_id, {"fields": fields}, None)


def _field_errors(field, value):
    key = field["key"]
    kind = field["type"]
    if kind == "boolean" and not isinstance(value, bool):
        return [{"key": key, "message": f"{key} must be true or false"}]
    if kind == "integer":
        if isinstance(value, bool) or not isinstance(value, int):
            return [{"key": key, "message": f"{key} must be an integer"}]
        if "min" in field and value < field["min"]:
            return [{"key": key, "message": f"{key} must be at least {field['min']}"}]
        if "max" in field and value > field["max"]:
            return [{"key": key, "message": f"{key} must be at most {field['max']}"}]
    if kind == "string" and not isinstance(value, str):
        return [{"key": key, "message": f"{key} must be a string"}]
    if kind == "enum" and value not in field["enum"]:
        allowed = ", ".join(field["enum"])
        return [{"key": key, "message": f"{key} must be one of: {allowed}"}]
    return []


def _apply(document, settings):
    for key, value in settings.items():
        if key.startswith("integrations."):
            document.setdefault("integrations", {})[key.split(".", 1)[1]] = value
        else:
            document.setdefault("preferences", {})[key] = value


def _current_value(document, field):
    key = field["key"]
    if key.startswith("integrations."):
        return (document.get("integrations") or {}).get(key.split(".", 1)[1], field["default"])
    return (document.get("preferences") or {}).get(key, field["default"])


def _validation_errors(data_root, settings):
    if not isinstance(settings, dict):
        return [{"key": "", "message": "settings must be a JSON object"}]
    errors = []
    for key, value in settings.items():
        field = _SCHEMA.get(key)
        if field is None:
            errors.append({"key": key, "message": f"Unknown setting '{key}'"})
            continue
        errors.extend(_field_errors(field, value))
    if errors:
        return errors
    try:
        document = ConfigStore(data_root).read()
        _apply(document, settings)
        validate_config(document)
    except (SelectionError, OSError, ValueError) as error:
        errors.append({"key": "", "message": str(error)})
    return errors


def _settings_digest(settings) -> str:
    payload = json.dumps(settings, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _op_validate(version, operation_id, data_root, payload):
    errors = _validation_errors(data_root, payload.get("settings"))
    return _reply(version, True, operation_id, {"valid": not errors, "errors": errors}, None)


def _op_apply(version, operation_id, data_root, payload):
    settings = payload.get("settings")
    errors = _validation_errors(data_root, settings)
    if errors:
        return _reply(version, False, operation_id, {"valid": False, "errors": errors},
                      _error("INVALID_SETTINGS", "The settings are not valid.",
                             "Fix the reported fields and retry."))
    digest = _settings_digest(settings)
    receipt_path = data_root / "receipts" / f"{operation_id}.json"
    if receipt_path.exists():
        try:
            stored = json.loads(receipt_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return _reply(version, False, operation_id, {},
                          _error("RECEIPT_UNREADABLE", "The stored receipt could not be read.",
                                 "Remove the corrupted receipt or use a new operation id."))
        if stored.get("settings_sha256") == digest:
            return _reply(version, True, operation_id, _flat(stored), None)
        return _reply(version, False, operation_id, {},
                      _error("OPERATION_ID_CONFLICT",
                             "This operation id was already used with different settings.",
                             "Use a new operation id for a different change."))
    try:
        ConfigStore(data_root).update(lambda document: _apply(document, settings))
    except (SelectionError, OSError, ValueError) as error:
        return _reply(version, False, operation_id, {},
                      _error("APPLY_FAILED", f"Settings could not be saved: {error}",
                             "Check that the data root is writable and retry."))
    receipt = {"operation_id": operation_id, "op": "settings.apply", "status": "applied",
               "applied_at": _now(), "settings_sha256": digest}
    try:
        atomic_write_json(receipt_path, receipt)
    except OSError as error:
        return _reply(version, False, operation_id, {"receipt": receipt},
                      _error("RECEIPT_FAILED", f"The receipt could not be written: {error}",
                             "Check that the data root is writable and retry."))
    return _reply(version, True, operation_id, _flat(receipt), None)


def _op_readback(version, operation_id, data_root):
    store = ConfigStore(data_root)
    try:
        document = store.read()
    except (SelectionError, OSError, ValueError) as error:
        return _reply(version, False, operation_id, {},
                      _error("READBACK_FAILED", f"Configuration could not be read: {error}",
                             "Check the data root and retry."))
    settings = {}
    for field in SETTINGS_FIELDS:
        value = _current_value(document, field)
        settings[field["key"]] = SECRET_MASK if field["secret"] and value else value
    source = "file" if store.path.exists() else "defaults"
    return _reply(version, True, operation_id, {"settings": settings, "source": source}, None)


def _op_lifecycle_plan(version, operation_id, data_root, payload):
    action = payload.get("action")
    if action not in lifecycle.ACTIONS:
        return _reply(version, False, operation_id, {},
                      _error("BAD_REQUEST", "Unknown lifecycle action.",
                             "Use one of: " + ", ".join(lifecycle.ACTIONS) + "."))
    result = lifecycle.plan(action, payload.get("target") or {})
    return _reply(version, True, operation_id, result, None)


def _op_lifecycle_apply(version, operation_id, data_root, payload):
    action = payload.get("action")
    if action not in lifecycle.ACTIONS:
        return _reply(version, False, operation_id, {},
                      _error("BAD_REQUEST", "Unknown lifecycle action.",
                             "Use one of: " + ", ".join(lifecycle.ACTIONS) + "."))
    if not isinstance(operation_id, str) or not _OPERATION_ID.match(operation_id):
        return _reply(version, False, operation_id, {},
                      _error("BAD_REQUEST",
                             "lifecycle.apply requires an operation_id of 8-64 characters [A-Za-z0-9_-].",
                             "Provide a unique operation_id."))
    try:
        receipt = lifecycle.apply(operation_id, action, payload.get("target") or {}, data_root)
    except lifecycle.LifecycleError as error:
        return _reply(version, False, operation_id, {}, _error(error.code, error.message, error.hint))
    return _reply(version, True, operation_id, receipt, None)


def _op_lifecycle_status(version, operation_id, data_root, payload):
    target = payload.get("operation_id") or operation_id
    if not isinstance(target, str) or not _OPERATION_ID.match(target):
        return _reply(version, False, operation_id, {},
                      _error("BAD_REQUEST", "An operation_id of 8-64 characters [A-Za-z0-9_-] is required.",
                             "Pass operation_id in the payload."))
    try:
        receipt = lifecycle.read_receipt(target, data_root)
    except lifecycle.LifecycleError as error:
        return _reply(version, False, operation_id, {}, _error(error.code, error.message, error.hint))
    return _reply(version, True, operation_id, receipt, None)


def _op_lifecycle_rollback(version, operation_id, data_root, payload):
    target = payload.get("operation_id") or operation_id
    if not isinstance(target, str) or not _OPERATION_ID.match(target):
        return _reply(version, False, operation_id, {},
                      _error("BAD_REQUEST", "An operation_id of 8-64 characters [A-Za-z0-9_-] is required.",
                             "Pass operation_id in the payload."))
    try:
        receipt = lifecycle.rollback(target, data_root)
    except lifecycle.LifecycleError as error:
        return _reply(version, False, operation_id, {}, _error(error.code, error.message, error.hint))
    return _reply(version, True, operation_id, receipt, None)


def _op_operation_receipt(version, operation_id, data_root, payload):
    target = payload.get("operation_id") or operation_id
    if not isinstance(target, str) or not _OPERATION_ID.match(target):
        return _reply(version, False, operation_id, {},
                      _error("BAD_REQUEST", "An operation_id of 8-64 characters [A-Za-z0-9_-] is required.",
                             "Pass operation_id in the payload."))
    try:
        receipt = lifecycle.read_receipt(target, data_root)
    except lifecycle.LifecycleError as error:
        return _reply(version, False, operation_id, {}, _error(error.code, error.message, error.hint))
    return _reply(version, True, operation_id, receipt, None)


def _op_integrations_plan(version, operation_id, data_root, payload):
    try:
        result = integrations.plan(data_root, payload.get("target") or {})
    except integrations.PlanError as error:
        return _reply(version, False, operation_id, {}, _error(error.code, error.message, error.hint))
    return _reply(version, True, operation_id, result, None)


def _memory_reply(version, operation_id, call):
    try:
        return _reply(version, True, operation_id, call(), None)
    except (memory.MemoryOpError, memory_grants.GrantError) as error:
        return _reply(version, False, operation_id, {}, _error(error.code, error.message, error.hint))


def _op_memory_grant(version, operation_id, data_root, payload):
    return _memory_reply(version, operation_id,
                         lambda: memory.grant(data_root, operation_id, payload))


def _op_memory_revoke(version, operation_id, data_root, payload):
    return _memory_reply(version, operation_id, lambda: memory.revoke(data_root, payload))


def _op_memory_write(version, operation_id, data_root, payload):
    return _memory_reply(version, operation_id, lambda: memory_write.write(data_root, operation_id, payload))


def _op_memory_write_revert(version, operation_id, data_root, payload):
    return _memory_reply(version, operation_id, lambda: memory_write.revert(data_root, payload))


def _op_memory_semantic_status(version, operation_id, data_root, payload):
    return _memory_reply(version, operation_id, lambda: memory_semantic.status(data_root))


def _op_memory_semantic_configure(version, operation_id, data_root, payload):
    return _memory_reply(version, operation_id, lambda: memory_semantic.configure(data_root, payload))


def _op_memory_semantic_pull(version, operation_id, data_root, payload):
    return _memory_reply(version, operation_id, lambda: memory_semantic.pull(data_root, payload))


def _op_memory_capture_run(version, operation_id, data_root, payload):
    return _memory_reply(version, operation_id, lambda: memory_capture.run(data_root, payload))


def _op_memory_search(version, operation_id, data_root, payload):
    return _memory_reply(version, operation_id, lambda: memory_workspace.search(data_root, payload))


def _op_memory_note_read(version, operation_id, data_root, payload):
    return _memory_reply(version, operation_id, lambda: memory_workspace.read(data_root, payload))


def _op_memory_capture_note(version, operation_id, data_root, payload):
    return _memory_reply(version, operation_id, lambda: memory_workspace.capture(data_root, operation_id, payload))


def _op_memory_briefing_run(version, operation_id, data_root, payload):
    return _memory_reply(version, operation_id, lambda: memory_workspace.briefing(data_root, payload))


def _op_memory_recall(version, operation_id, data_root, payload):
    return _memory_reply(version, operation_id, lambda: memory.recall(data_root, payload))


def _index_reply(version, operation_id, call):
    try:
        return _reply(version, True, operation_id, call(), None)
    except memory_index.MemoryIndexError as error:
        return _reply(version, False, operation_id, {}, _error(error.code, error.message, error.hint))


def _op_memory_index_status(version, operation_id, data_root, payload):
    return _index_reply(version, operation_id, lambda: memory_index.status(data_root))


def _op_memory_index_refresh(version, operation_id, data_root, payload):
    return _index_reply(version, operation_id,
                        lambda: memory_index.refresh(data_root, operation_id, payload))


_V11_OPS = {
    "memory.index.status": _op_memory_index_status,
    "memory.index.refresh": _op_memory_index_refresh,
    "memory.grant": _op_memory_grant,
    "memory.revoke": _op_memory_revoke,
    "memory.recall": _op_memory_recall,
    "memory.semantic.status": _op_memory_semantic_status,
    "memory.semantic.configure": _op_memory_semantic_configure,
    "memory.semantic.pull": _op_memory_semantic_pull,
    "memory.capture.run": _op_memory_capture_run,
    "memory.search": _op_memory_search,
    "memory.note.read": _op_memory_note_read,
    "memory.capture.note": _op_memory_capture_note,
    "memory.briefing.run": _op_memory_briefing_run,
    "memory.write": _op_memory_write,
    "memory.write.revert": _op_memory_write_revert,
    "integrations.plan": _op_integrations_plan,
    "lifecycle.plan": _op_lifecycle_plan,
    "lifecycle.apply": _op_lifecycle_apply,
    "lifecycle.status": _op_lifecycle_status,
    "lifecycle.rollback": _op_lifecycle_rollback,
    "operation.receipt": _op_operation_receipt,
}


def _dispatch(version, request, data_root):
    operation_id = request.get("operation_id")
    op = request.get("op")
    payload = request.get("payload")
    if not isinstance(op, str):
        return _reply(version, False, operation_id, {},
                      _error("BAD_REQUEST", "The request is missing a string 'op'.",
                             "Send {'rpp':'1.0','op':'manifest'}."))
    if payload is not None and not isinstance(payload, dict):
        return _reply(version, False, operation_id, {},
                      _error("BAD_REQUEST", "payload must be a JSON object.",
                             "Send payload as an object."))
    if op in _V11_OPS:
        if version != PROTOCOL_MAX:
            return _reply(version, False, operation_id, {},
                          _error("UNSUPPORTED_OP", f"'{op}' requires protocol 1.1.",
                                 f"Send rpp '{PROTOCOL_MAX}' to use '{op}'."))
        return _V11_OPS[op](version, operation_id, data_root, payload or {})
    if op == "manifest":
        return _op_manifest(version, operation_id, data_root)
    if op == "health":
        return _op_health(version, operation_id, data_root)
    if op == "settings.schema":
        return _op_schema(version, operation_id)
    if op == "settings.validate":
        return _op_validate(version, operation_id, data_root, payload or {})
    if op == "settings.apply":
        if not isinstance(operation_id, str) or not _OPERATION_ID.match(operation_id):
            return _reply(version, False, operation_id, {},
                          _error("BAD_REQUEST",
                                 "settings.apply requires an operation_id of 8-64 characters [A-Za-z0-9_-].",
                                 "Provide a unique operation_id."))
        return _op_apply(version, operation_id, data_root, payload or {})
    if op == "settings.readback":
        return _op_readback(version, operation_id, data_root)
    return _reply(version, False, operation_id, {},
                  _error("UNKNOWN_OP", f"Unknown op '{op}'.",
                         "Use one of: " + ", ".join(_V10_OPS + tuple(_V11_OPS)) + "."))


def serve(raw=None, *, data_root=None):
    """Handle one request and return a response dict. Never raises."""
    try:
        text = raw if raw is not None else sys.stdin.read()
    except (OSError, ValueError):
        text = ""
    try:
        request = json.loads(text) if text and text.strip() else None
    except ValueError:
        request = None
    if not isinstance(request, dict):
        return _reply(PROTOCOL_MIN, False, None, {},
                      _error("BAD_REQUEST", "The request must be a single JSON object.",
                             "Send one JSON request on stdin."))
    operation_id = request.get("operation_id")
    requested = request.get("rpp")
    if requested not in (PROTOCOL_MIN, PROTOCOL_MAX):
        return _reply(PROTOCOL_MIN, False, operation_id, {},
                      _error("PROTOCOL_UNSUPPORTED", "Unsupported protocol version.",
                             f"Use rpp version '{PROTOCOL_MIN}' or '{PROTOCOL_MAX}'."))
    try:
        resolved = _resolve_data_root(data_root)
    except (FoundationError, SelectionError, OSError, ValueError) as error:
        return _reply(requested, False, operation_id, {},
                      _error("ROOT_UNRESOLVED", f"The data root could not be resolved: {error}",
                             "Pass --data-root or set RESPECTED_RPP_DATA_ROOT."))
    try:
        return _dispatch(requested, request, resolved)
    except Exception as error:  # never leak a traceback to the caller
        return _reply(requested, False, operation_id, {},
                      _error("INTERNAL_ERROR",
                             f"Unexpected {type(error).__name__} while handling '{request.get('op')}'.",
                             "Retry or report this problem."))


def main(*, data_root=None) -> int:
    response = serve(data_root=data_root)
    sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
    sys.stdout.flush()
    return 0
