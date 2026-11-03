"""Respected Product Protocol (RPP) 1 server for Respected Brain.

One JSON request on stdin, one JSON response line on stdout; no listener, no daemon. Settings go through
`respected_brain.settings`, the same code as the `config` command and the installer. Installing, repairing and
removing are the installer's work, not protocol operations.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .. import settings as product_settings
from ..core.config import ConfigStore, atomic_write_json
from ..core.errors import FoundationError, SelectionError
# The memory, search and integration modules are imported inside the operations that use them: a manifest or health call must not load them.

RPP = "1"
PRODUCT_ID = "respected-brain"
_OPERATION_ID = re.compile(r"^[A-Za-z0-9_-]{8,64}$")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _product_version() -> str:
    from .. import __version__
    return __version__


def _reply(ok, operation_id, result, error) -> dict:
    return {"rpp": RPP, "ok": ok, "operation_id": operation_id,
            "result": result if error is None else None, "error": error}


def _error(code, message, hint) -> dict:
    return {"code": code, "message": message, "hint": hint}


def install_state(data_root: Path) -> dict:
    """Installed = the product's install record exists; repair-needed = a recorded program file is missing or changed."""
    from ..bootstrap import application_roots
    manifest = data_root / "install-manifest.json"
    installed = manifest.is_file()
    vault = None
    try:
        document = ConfigStore(data_root).read()
        entry = (document.get("vaults") or {}).get(document.get("active_vault_id"))
        vault = str(entry["path"]) if entry else None
    except (SelectionError, OSError, ValueError):
        pass
    state = "absent"
    if installed:
        state = "repair-needed" if _owned_files_changed(manifest) else "installed"
    return {"installed": installed, "install_state": state,
            "roots": {"app": str(application_roots().app_root), "data": str(data_root), "vault": vault}}


def _owned_files_changed(manifest: Path) -> bool:
    # every Hub call lands here: a file whose size and mtime are those of its last matching hash is not hashed again
    cache = manifest.with_name(".verified-files.json")
    try:
        seen = json.loads(cache.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        seen = {}
    if not isinstance(seen, dict):
        seen = {}
    fresh = {}
    try:
        for row in json.loads(manifest.read_text(encoding="utf-8")).get("files", []):
            if row.get("role") not in ("application", "launcher"):
                continue  # technical files such as config.json legitimately change
            path = Path(row["path"])
            if not path.is_file():
                return True
            stat = path.stat()
            key = [stat.st_size, stat.st_mtime_ns, row["sha256"]]
            if seen.get(row["path"]) != key and hashlib.sha256(path.read_bytes()).hexdigest() != row["sha256"]:
                return True
            fresh[row["path"]] = key
    except (OSError, ValueError, KeyError, TypeError):
        return True
    if fresh != seen:
        try:
            atomic_write_json(cache, fresh)
        except OSError:
            pass
    return False


def _op_manifest(operation_id, data_root, payload):
    result = {"product_id": PRODUCT_ID, "product_version": _product_version(), "rpp": RPP,
              "capabilities": sorted(_OPS), **install_state(data_root)}
    return _reply(True, operation_id, result, None)


_SAFE_CODE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,63}\Z")


def _safe_code(value, default="unclassified"):
    text = str(value or "")
    return text if _SAFE_CODE.fullmatch(text) else default


def _check(name, ok, detail, category, hint):
    return {"name": name, "ok": bool(ok), "detail": detail, "category": category, "hint": hint}


def _json_object(path):
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return None
    return loaded if isinstance(loaded, dict) else None


def _vault_state_dir(data_root, document):
    identity = document.get("active_vault_id") if document else None
    if not isinstance(identity, str):
        return None
    try:
        identity = str(uuid.UUID(identity))
    except ValueError:
        return None
    return data_root / "vaults" / identity / "state"


def _epoch_text(value):
    try:
        return datetime.fromtimestamp(float(value), tz=timezone.utc).isoformat(timespec="seconds")
    except (TypeError, ValueError, OSError, OverflowError):
        return ""


def _iso_text(value):
    if not isinstance(value, str):
        return ""
    try:
        return datetime.fromisoformat(value).isoformat(timespec="seconds")
    except ValueError:
        return ""


def _latest_capture(state_dir):
    try:
        paths = list(state_dir.glob("flush-*.json"))
    except OSError:
        return None
    newest = None
    for path in paths:
        record = _json_object(path)
        if record is not None and isinstance(record.get("ts"), (int, float)):
            if newest is None or float(record["ts"]) > float(newest["ts"]):
                newest = record
    return newest


def _capture_integration_check(document, integrations):
    hooks = integrations.get("global") is True
    mcp = integrations.get("mcp") is True
    clients = integrations.get("clients")
    names = ",".join(_safe_code(client, "") for client in clients if isinstance(client, str)) if isinstance(clients, list) else ""
    detail = "Configuration unavailable" if document is None else (
        f"Hooks: {'on' if hooks else 'off'}; MCP: {'on' if mcp else 'off'}; Clients: {names or 'all detected'}")
    hint = "Hub'da Yakalama'y\u0131 a\u00e7\u0131n ve AI arac\u0131nda Respected hook iznini onaylay\u0131n."
    return _check("capture_integration", document is not None and hooks, detail, "capture", hint)


def _last_capture_check(state_dir):
    record = _latest_capture(state_dir) if state_dir else None
    if record is None:
        return _check("last_capture", True, "No capture recorded yet", "capture",
                      "Bir AI arac\u0131nda oturumu tamamlay\u0131n; oturum sonu yakalamay\u0131 tetikler.")
    status = _safe_code(record.get("status"), "unknown")
    code = _safe_code(record.get("detail"), "")
    when = _epoch_text(record.get("ts"))
    if status == "ok":
        if code == "below-minimum-turns":
            detail = "Last session was skipped: too few turns"
        elif code == "flush-bos":
            detail = "Last session was skipped: summary was empty"
        else:
            detail = f"Last capture succeeded{' at ' + when if when else ''}"
        return _check("last_capture", True, detail, "capture", "")
    if status == "archived":
        return _check("last_capture", True, "Last session was archived without a summary", "capture", "")
    if status == "pending":
        return _check("last_capture", False, f"Last capture is pending ({code or 'unknown'})", "capture",
                      "Yar\u0131m kalan i\u015flemi respected-brain recover ile geri al\u0131n; \u00f6zetleyiciyi kontrol edin.")
    return _check("last_capture", False, f"Last capture failed ({code or status})", "capture",
                  "Sa\u011flay\u0131c\u0131 ayar\u0131n\u0131 ve logs klas\u00f6r\u00fcndeki g\u00fcvenli \u00f6zeti kontrol edin; gerekirse respected-brain recover \u00e7al\u0131\u015ft\u0131r\u0131n.")


def _pipeline_check(state_dir):
    path = state_dir / "health.json" if state_dir else None
    if path is None or not path.is_file():
        return _check("memory_pipeline", True, "No pipeline errors recorded", "pipeline", "")
    payload = _json_object(path)
    if payload is None:
        return _check("memory_pipeline", False, "Pipeline health record is unreadable", "pipeline",
                      "respected-brain repair ile \u00e7al\u0131\u015fma kay\u0131tlar\u0131n\u0131 yenileyin.")
    warnings = payload.get("warnings")
    warning_count = len(warnings) if isinstance(warnings, list) else 0
    if payload.get("status") == "degraded" or (payload.get("error") and not warning_count):
        code = _safe_code(payload.get("reason") or payload.get("error"))
        stage = _safe_code(payload.get("stage"), "memory")
        return _check("memory_pipeline", False, f"Pipeline problem: {code} ({stage})", "pipeline",
                      "Sa\u011flay\u0131c\u0131 ayar\u0131n\u0131 ve logs klas\u00f6r\u00fcndeki g\u00fcvenli \u00f6zeti kontrol edin; yar\u0131m i\u015flem varsa respected-brain recover \u00e7al\u0131\u015ft\u0131r\u0131n.")
    detail = f"Pipeline has {warning_count} warning(s)" if warning_count else "No pipeline errors recorded"
    return _check("memory_pipeline", True, detail, "pipeline", "")


def _index_check(state_dir, data_root):
    hint = "Aramada eski sonu\u00e7 g\u00f6r\u00fcrseniz respected-brain index-refresh \u00e7al\u0131\u015ft\u0131r\u0131n."
    missing = _check("index_freshness", True, "Search index is not built yet; the first search builds it", "index", hint)
    if state_dir is None:
        return missing
    index_db = state_dir.parent / "cache" / "search_index.db"
    try:
        present = index_db.is_file()
        size = index_db.stat().st_size if present else 0
    except OSError:
        return missing
    if not present:
        return missing
    if size == 0:
        return _check("index_freshness", False, "Search index file is empty", "index",
                      "respected-brain index-refresh ile arama dizinini yeniden kurun.")
    refresh = _json_object(data_root / "memory-index-refresh.json")
    at = _iso_text(refresh.get("at")) if refresh else ""
    detail = f"Search index refreshed at {at}" if at else "Search index present; last refresh time unknown"
    return _check("index_freshness", True, detail, "index", "")


def _health_checks(data_root, document):
    integrations = (document or {}).get("integrations")
    integrations = integrations if isinstance(integrations, dict) else {}
    checks = [_capture_integration_check(document, integrations)]
    state_dir = _vault_state_dir(data_root, document)
    checks.append(_last_capture_check(state_dir))
    checks.append(_pipeline_check(state_dir))
    checks.append(_index_check(state_dir, data_root))
    return checks


def _op_health(operation_id, data_root, payload):
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
    checks.append(_check("data_root_writable", writable, detail, "storage",
                         "Veri klasörünün yazılabilir olduğundan emin olun; izinleri respected-brain repair ile yenileyin."))
    document = None
    config_detail = "Configuration loaded"
    try:
        document = ConfigStore(data_root).read()
    except (SelectionError, OSError, ValueError) as error:
        config_detail = f"Configuration unavailable: {error}"
    checks.append(_check("config_loads", document is not None, config_detail, "config",
                         "respected-brain repair ayarları ve kurulum kaydını yeniden okur."))
    entry = (document.get("vaults") or {}).get(document.get("active_vault_id")) if document else None
    checks.append(_check("vault_registered", bool(entry),
                         f"Vault registered: {entry['path']}" if entry else "No active vault configured", "vault",
                         "Hub'da bir not kasası seçin ya da respected-brain repair çalıştırın."))
    if entry:  # a notes folder on a drive that is unplugged (or was moved) is not a healthy product
        present = Path(entry["path"]).is_dir()
        checks.append(_check("vault_folder", present,
                             "Vault folder is present" if present else f"Vault folder not found (drive disconnected?): {entry['path']}", "vault",
                             "Kasanın bulunduğu sürücüyü (ör. USB) takın ya da klasörü eski yerine koyun."))
    checks.extend(_health_checks(data_root, document))
    if not writable or document is None:
        status = "unhealthy"
    elif all(check["ok"] for check in checks):
        status = "healthy"
    else:
        status = "degraded"
    recovery = [{"check": check["name"], "category": check["category"], "action": check["hint"]}
                for check in checks if not check["ok"] and check["hint"]]
    return _reply(True, operation_id, {"status": status, "version": _product_version(), "checks": checks,
                                       "recovery": recovery}, None)


def _op_schema(operation_id, data_root, payload):
    return _reply(True, operation_id, {"fields": product_settings.schema()}, None)


def _op_validate(operation_id, data_root, payload):
    errors = product_settings.validate(data_root, payload.get("settings"))
    return _reply(True, operation_id, {"valid": not errors, "errors": errors}, None)


def _settings_digest(values) -> str:
    return hashlib.sha256(json.dumps(values, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


def _op_apply(operation_id, data_root, payload):
    values = payload.get("settings")
    if not isinstance(operation_id, str) or not _OPERATION_ID.match(operation_id):
        return _reply(False, operation_id, {}, _error("BAD_REQUEST", "settings.apply requires an operation_id of 8-64 characters [A-Za-z0-9_-].",
                                                      "Provide a unique operation_id."))
    receipt_path = data_root / "receipts" / f"{operation_id}.json"
    digest = _settings_digest(values)
    if receipt_path.exists():  # the same request again is answered from its receipt, never applied twice
        try:
            stored = json.loads(receipt_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return _reply(False, operation_id, {}, _error("RECEIPT_UNREADABLE", "The stored receipt could not be read.",
                                                          "Remove the corrupted receipt or use a new operation id."))
        if stored.get("settings_sha256") == digest:
            return _reply(True, operation_id, stored, None)
        return _reply(False, operation_id, {}, _error("OPERATION_ID_CONFLICT", "This operation id was already used with different settings.",
                                                      "Use a new operation id for a different change."))
    try:
        product_settings.apply(data_root, values)
    except product_settings.SettingsError as error:
        return _reply(False, operation_id, {"valid": False, "errors": error.errors},
                      _error("INVALID_SETTINGS", str(error), "Fix the reported fields and retry."))
    except (FoundationError, SelectionError, OSError, ValueError) as error:
        return _reply(False, operation_id, {}, _error("APPLY_FAILED", f"Settings could not be saved: {error}",
                                                      "Check that the data root is writable and retry."))
    receipt = {"status": "applied", "applied_at": _now(), "settings_sha256": digest}
    try:
        atomic_write_json(receipt_path, receipt)
    except OSError as error:
        return _reply(False, operation_id, {"receipt": receipt}, _error("RECEIPT_FAILED", f"The receipt could not be written: {error}",
                                                                        "Check that the data root is writable and retry."))
    return _reply(True, operation_id, receipt, None)


def _op_readback(operation_id, data_root, payload):
    try:
        values = product_settings.readback(data_root)
    except (SelectionError, OSError, ValueError) as error:
        return _reply(False, operation_id, {}, _error("READBACK_FAILED", f"Configuration could not be read: {error}",
                                                      "Check the data root and retry."))
    return _reply(True, operation_id, {"settings": values}, None)


def _op_integrations_plan(operation_id, data_root, payload):
    from . import integrations
    try:
        result = integrations.plan(data_root, payload.get("target") or {})
    except integrations.PlanError as error:
        return _reply(False, operation_id, {}, _error(error.code, error.message, error.hint))
    return _reply(True, operation_id, result, None)


def _memory_reply(operation_id, call):
    from . import memory, memory_grants
    try:
        return _reply(True, operation_id, call(), None)
    except (memory.MemoryOpError, memory_grants.GrantError) as error:
        return _reply(False, operation_id, {}, _error(error.code, error.message, error.hint))


def _op_memory_grant(operation_id, data_root, payload):
    from . import memory
    return _memory_reply(operation_id,
                         lambda: memory.grant(data_root, operation_id, payload))


def _op_memory_revoke(operation_id, data_root, payload):
    from . import memory
    return _memory_reply(operation_id, lambda: memory.revoke(data_root, payload))


def _op_memory_write(operation_id, data_root, payload):
    from . import memory_write
    return _memory_reply(operation_id, lambda: memory_write.write(data_root, operation_id, payload))


def _op_memory_write_revert(operation_id, data_root, payload):
    from . import memory_write
    return _memory_reply(operation_id, lambda: memory_write.revert(data_root, payload))


def _op_memory_semantic_status(operation_id, data_root, payload):
    from . import memory_semantic
    return _memory_reply(operation_id, lambda: memory_semantic.status(data_root))


def _op_memory_semantic_configure(operation_id, data_root, payload):
    from . import memory_semantic
    return _memory_reply(operation_id, lambda: memory_semantic.configure(data_root, payload))


def _op_memory_semantic_pull(operation_id, data_root, payload):
    from . import memory_semantic
    return _memory_reply(operation_id, lambda: memory_semantic.pull(data_root, payload))


def _op_memory_capture_run(operation_id, data_root, payload):
    from . import memory_capture
    return _memory_reply(operation_id, lambda: memory_capture.run(data_root, payload))


def _op_memory_search(operation_id, data_root, payload):
    from . import memory_workspace
    return _memory_reply(operation_id, lambda: memory_workspace.search(data_root, payload))


def _op_memory_note_read(operation_id, data_root, payload):
    from . import memory_workspace
    return _memory_reply(operation_id, lambda: memory_workspace.read(data_root, payload))


def _op_memory_capture_note(operation_id, data_root, payload):
    from . import memory_workspace
    return _memory_reply(operation_id, lambda: memory_workspace.capture(data_root, operation_id, payload))


def _op_memory_briefing_run(operation_id, data_root, payload):
    from . import memory_workspace
    return _memory_reply(operation_id, lambda: memory_workspace.briefing(data_root, payload))


def _op_memory_review_queue(operation_id, data_root, payload):
    from . import memory_workspace
    return _memory_reply(operation_id, lambda: memory_workspace.review_queue(data_root, payload))


def _op_memory_review_apply(operation_id, data_root, payload):
    from . import memory_workspace
    return _memory_reply(operation_id, lambda: memory_workspace.review_apply(data_root, operation_id, payload))


def _op_memory_recall(operation_id, data_root, payload):
    from . import memory
    return _memory_reply(operation_id, lambda: memory.recall(data_root, payload))


def _index_reply(operation_id, call):
    from . import memory_index
    try:
        return _reply(True, operation_id, call(), None)
    except memory_index.MemoryIndexError as error:
        return _reply(False, operation_id, {}, _error(error.code, error.message, error.hint))


def _op_memory_index_status(operation_id, data_root, payload):
    from . import memory_index
    return _index_reply(operation_id, lambda: memory_index.status(data_root))


def _op_memory_index_refresh(operation_id, data_root, payload):
    from . import memory_index
    return _index_reply(operation_id,
                        lambda: memory_index.refresh(data_root, operation_id, payload))


_OPS = {
    "manifest": _op_manifest,
    "health": _op_health,
    "settings.schema": _op_schema,
    "settings.validate": _op_validate,
    "settings.apply": _op_apply,
    "settings.readback": _op_readback,
    "integrations.plan": _op_integrations_plan,
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
    "memory.review.queue": _op_memory_review_queue,
    "memory.review.apply": _op_memory_review_apply,
    "memory.write": _op_memory_write,
    "memory.write.revert": _op_memory_write_revert,
}


def serve(raw=None, *, data_root=None):
    """Handle one request and return a response dict. Never raises. `data_root` is for in-process tests only."""
    try:
        text = raw if raw is not None else sys.stdin.read()
        request = json.loads(text) if text and text.strip() else None
    except (OSError, ValueError, RecursionError):  # deeply nested JSON raises RecursionError, which is not a ValueError
        request = None
    if not isinstance(request, dict):
        return _reply(False, None, {}, _error("BAD_REQUEST", "The request must be a single JSON object.", "Send one JSON request on stdin."))
    operation_id = request.get("operation_id")
    if request.get("rpp") != RPP:
        return _reply(False, operation_id, {}, _error("UNSUPPORTED_VERSION", "Unsupported protocol version.", f"Send rpp '{RPP}'."))
    op, payload = request.get("op"), request.get("payload")
    handler = _OPS.get(op) if isinstance(op, str) else None
    if handler is None:
        return _reply(False, operation_id, {}, _error("UNKNOWN_OP", f"Unknown op '{op}'.", "Use one of: " + ", ".join(sorted(_OPS)) + "."))
    if payload is not None and not isinstance(payload, dict):
        return _reply(False, operation_id, {}, _error("BAD_REQUEST", "payload must be a JSON object.", "Send payload as an object."))
    try:
        if data_root is None:
            from ..bootstrap import application_roots
            data_root = application_roots().data_root
        return handler(operation_id, Path(data_root), payload or {})
    except Exception as error:  # never leak a traceback to the caller
        return _reply(False, operation_id, {}, _error("INTERNAL_ERROR", f"Unexpected {type(error).__name__} while handling '{op}'.",
                                                      "Retry or report this problem."))


def main() -> int:
    sys.stdout.write(json.dumps(serve(), ensure_ascii=False) + "\n")
    sys.stdout.flush()
    return 0
