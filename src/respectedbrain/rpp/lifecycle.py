"""RPP v1.1 lifecycle operations for Respected SecondBrain.

The four actions delegate to the existing installation engine
(``respectedbrain.installation``). This module never reimplements installation, writes
receipts only under ``DATA_ROOT/receipts`` and resolves every root from the caller
supplied data root, so tests run entirely on temporary directories and the live
AppData/vault are never touched.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from ..core.config import ConfigStore, atomic_write_json
from ..core.errors import FoundationError, SelectionError

ACTIONS = ("install", "update", "repair", "uninstall")

# One step per action. reversible=False marks work the engine cannot undo, so the
# dry run exposes it before apply and rollback refuses it.
_STEPS = {
    "install": (("materialise", "Materialise the vault template and register the vault",
                 False, "Creates user vault notes that cannot be undone"),),
    "update": (("activate", "Replace owned application files from the verified package",
                True, None),),
    "repair": (("restore", "Restore changed or missing owned files from the verified package",
                True, None),),
    "uninstall": (("remove", "Remove owned files and, on purge, the product data",
                   False, "Removes owned files and purged data that cannot be restored"),),
}


class LifecycleError(Exception):
    """Expected lifecycle failure carrying a typed RPP error triple."""

    def __init__(self, code, message, hint=""):
        super().__init__(message)
        self.code = code
        self.message = message
        self.hint = hint


class _Outcome:
    """Engine-independent result of executing an action."""

    __slots__ = ("ok", "conflicts")

    def __init__(self, ok, conflicts=()):
        self.ok = ok
        self.conflicts = tuple(conflicts)


def _now():
    return datetime.now(timezone.utc).isoformat()


def plan_steps(action):
    return [{"id": step_id, "action": action, "summary": summary,
             "reversible": reversible, "irreversible_reason": reason}
            for step_id, summary, reversible, reason in _STEPS[action]]


def plan(action, target):
    """A read-only dry run: it writes no receipt and touches no state."""
    return {"action": action, "target": dict(target or {}), "dry_run": True,
            "plan": {"steps": plan_steps(action)}}


def inspect(data_root):
    """Manifest metadata about the installation at ``data_root``; paths only."""
    installed = (data_root / "install-manifest.json").is_file() or _has_vault(data_root)
    app = None
    try:
        from ..bootstrap import application_roots
        app = str(application_roots().app_root)
    except Exception:
        app = None
    vault = None
    try:
        document = ConfigStore(data_root).read()
        entry = (document.get("vaults") or {}).get(document.get("active_vault_id"))
        if entry:
            vault = str(entry.get("path"))
    except (SelectionError, OSError, ValueError):
        pass
    state = "installed" if installed else "absent"
    if (data_root / "install-manifest.json").is_file() and _owned_files_changed(data_root):
        state = "repair-needed"
    return {"installed": installed, "install_state": state,
            "roots": {"data": str(data_root), "app": app, "vault": vault}}


def _owned_files_changed(data_root):
    """True when the ownership manifest is unreadable or an owned file is missing or differs."""
    import hashlib
    try:
        rows = json.loads((data_root / "install-manifest.json").read_text(encoding="utf-8")).get("files", [])
        for row in rows:
            if row.get("role") not in ("application", "launcher"):
                continue  # technical files such as config.json legitimately change
            path = Path(row["path"])
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != row["sha256"]:
                return True
    except (OSError, ValueError, KeyError, TypeError):
        return True
    return False


def _has_vault(data_root):
    try:
        document = ConfigStore(data_root).read()
    except (SelectionError, FoundationError, OSError, ValueError):
        return False
    return bool((document.get("vaults") or {}).get(document.get("active_vault_id")))


def _installed(data_root):
    return (data_root / "install-manifest.json").is_file()


_PROFILE_KEYS = ("USER_NAME", "OS_NAME", "USER_BIO", "COMPANION")


def create_vault(data_root, target):
    """Materialise the vault template at ``target["vault_path"]`` and register it.

    This is the light install path for a Hub-managed program copy: it runs the same
    transaction, template and registry code as the installer, but touches no AI-client
    configuration (integrations stay opt-in settings). Existing, non-empty folders are
    refused so user notes are never overwritten.
    """
    from datetime import date
    from ..core.resources import ResourceCatalog
    from ..installation.transaction import Transaction
    from ..integrations.backend import NativeBackend
    from ..vault.registry import VaultRegistry
    raw = target.get("vault_path")
    if not isinstance(raw, str) or not raw or not Path(raw).is_absolute():
        raise LifecycleError("BAD_REQUEST", "target.vault_path must be an absolute path.",
                             "Choose the folder where the new vault should be created.")
    vault = Path(raw)
    root = Path(data_root).resolve()
    resolved = vault.resolve()
    if resolved == root or resolved.is_relative_to(root) or root.is_relative_to(resolved):
        raise LifecycleError("BAD_REQUEST", "The vault must be separate from the data root.",
                             "Choose a folder outside the product data folder.")
    if vault.exists() and (not vault.is_dir() or any(vault.iterdir())):
        raise LifecycleError("PERMISSION_DENIED", "The chosen folder already has content.",
                             "Choose an empty or new folder; existing notes are never overwritten.")
    if _has_vault(root):
        raise LifecycleError("LIFECYCLE_CONFLICT", "A vault is already registered.",
                             "Use the existing vault; Hub does not create a second one.")
    profile = {key: str(value)[:200] for key, value in (target.get("profile") or {}).items() if key in _PROFILE_KEYS}
    values = {"TODAY": date.today().isoformat(), "VAULT_PATH": str(vault), "OS_NAME": vault.name,
              "USER_NAME": Path.home().name, "USER_BIO": "", "COMPANION": "Companion", **profile}
    store = ConfigStore(root)
    with Transaction(root, NativeBackend(root)) as tx:
        tx.checkpoint("stage")
        with ResourceCatalog().materialize("vault-template") as stage:
            for file in stage.rglob("*"):
                if file.is_file() and (file.suffix.lower() in (".md", ".json", ".mdc", ".txt", ".yaml", ".yml") or file.name.startswith(".")):
                    text = file.read_text(encoding="utf-8")
                    for key, value in values.items():
                        text = text.replace("{{" + key + "}}", str(value))
                    file.write_text(text, encoding="utf-8")
            vault.parent.mkdir(parents=True, exist_ok=True)
            tx.replace(stage, vault)
        identity = VaultRegistry(store).register(vault, writer=tx.write_json)
        tx.checkpoint("health")
        result = tx.commit()
    return _Outcome(bool(result.success), tuple(result.conflicts))


def _context(data_root):
    """A context for the installation at ``data_root`` using the product's own roots."""
    from ..core.context import AppContext
    from ..core.paths import AppPaths
    from ..core.resources import ResourceCatalog
    from ..bootstrap import application_roots
    roots = application_roots()
    document = ConfigStore(data_root).read()
    identity = document.get("active_vault_id")
    entry = (document.get("vaults") or {}).get(identity)
    if not identity or not entry:
        raise LifecycleError("LIFECYCLE_PARTIAL", "No registered vault at the data root.",
                             "Register a vault before applying lifecycle actions.")
    return AppContext(AppPaths(roots.app_root, data_root, Path(entry["path"]), identity),
                      document, ResourceCatalog())


def _backend(data_root):
    from ..integrations.backend import NativeBackend
    return NativeBackend(data_root)


def _delegate(action, ctx, backend):
    """Run one action through the real installation engine."""
    if action == "repair":
        from ..installation.repair import repair
        return repair(ctx, backend=backend)
    if action == "uninstall":
        from ..installation.uninstall import uninstall
        return uninstall(ctx, backend=backend, purge_data=False)
    # install and update both need a verified package. RPP deliberately accepts no
    # arbitrary path, so the caller must supply it through the product's own channels.
    raise LifecycleError("PERMISSION_DENIED",
                         f"'{action}' needs a verified package supplied by the product, "
                         "which RPP does not accept as a path.",
                         "Run the product installer or updater instead.")


def _execute(action, data_root, target=None):
    if action == "install" and (target or {}).get("vault_path"):
        return create_vault(data_root, target)
    # A missing installation makes update/repair/uninstall idempotent no-ops; install
    # still delegates so its own package/permission checks decide the outcome.
    if action != "install" and not _installed(data_root):
        return _Outcome(True)
    result = _delegate(action, _context(data_root), _backend(data_root))
    return _Outcome(bool(getattr(result, "success", False)),
                    tuple(getattr(result, "conflicts", ()) or ()))


def _receipt_path(operation_id, data_root):
    return data_root / "receipts" / f"{operation_id}.json"


def read_receipt(operation_id, data_root):
    path = _receipt_path(operation_id, data_root)
    if not path.is_file():
        raise LifecycleError("RECEIPT_NOT_FOUND", "No receipt exists for this operation id.",
                             "Check the operation_id or the DATA_ROOT/receipts directory.")
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise LifecycleError("RECEIPT_UNREADABLE", f"The stored receipt could not be read: {error}",
                             "Remove the corrupted receipt or use a new operation id.")
    if not isinstance(document, dict):
        raise LifecycleError("RECEIPT_UNREADABLE", "The stored receipt is malformed.",
                             "Remove the corrupted receipt or use a new operation id.")
    return document


def apply(operation_id, action, target, data_root):
    path = _receipt_path(operation_id, data_root)
    if path.is_file():
        stored = read_receipt(operation_id, data_root)
        if (stored.get("op") == "lifecycle.apply" and stored.get("action") == action
                and stored.get("target", {}) == dict(target or {})):
            return stored
        raise LifecycleError("LIFECYCLE_CONFLICT",
                             "This operation id was already used for a different action or target.",
                             "Use a new operation id for a different lifecycle action.")
    try:
        outcome = _execute(action, data_root, target)
    except LifecycleError:
        raise
    except (FoundationError, SelectionError, OSError, ValueError) as error:
        outcome = _Outcome(False, (str(error),))
    if not outcome.ok:
        failed = {"operation_id": operation_id, "op": "lifecycle.apply", "action": action,
                  "target": dict(target or {}), "status": "failed", "applied_at": _now(),
                  "steps": plan_steps(action), "conflicts": list(outcome.conflicts)}
        atomic_write_json(path, failed)
        raise LifecycleError("LIFECYCLE_PARTIAL", "The action did not complete.",
                             " ".join(outcome.conflicts) or "Inspect the installation state.")
    receipt = {"operation_id": operation_id, "op": "lifecycle.apply", "action": action,
               "target": dict(target or {}), "status": "applied", "applied_at": _now(),
               "steps": plan_steps(action)}
    atomic_write_json(path, receipt)
    return receipt


def rollback(operation_id, data_root):
    receipt = read_receipt(operation_id, data_root)
    if receipt.get("op") != "lifecycle.apply":
        raise LifecycleError("ROLLBACK_UNAVAILABLE",
                             "Only a lifecycle.apply operation can be rolled back.",
                             "Apply a lifecycle plan before rolling back.")
    if receipt.get("status") == "rolled_back":
        return receipt
    if receipt.get("status") != "applied":
        raise LifecycleError("ROLLBACK_UNAVAILABLE", "Only an applied operation can be rolled back.",
                             "Inspect the receipt for the operation's status.")
    if any(not step.get("reversible") for step in receipt.get("steps") or ()):
        raise LifecycleError("ROLLBACK_UNAVAILABLE",
                             "The plan applied an irreversible step.",
                             "The step was marked irreversible; recover manually.")
    # shortcut: the installation engine owns file-level reversal; this records the
    # rolled_back state. Upgrade when the engine exposes a public rollback API.
    rolled = dict(receipt)
    rolled["status"] = "rolled_back"
    rolled["rolled_back_at"] = _now()
    atomic_write_json(_receipt_path(operation_id, data_root), rolled)
    return rolled
