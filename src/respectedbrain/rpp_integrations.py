"""RPP v1.1 ``integrations.plan``: a read-only Safe Integration Layer preview.

Discover -> Inspect -> Plan -> Explain: for the requested integrations it reports which AI-client
configuration files exist, exactly which ones Respected would create or change, and why a change
would be refused (unknown or user-modified entries). It writes nothing: no receipt, no config.
The apply step is the installer itself (``setup``/``update``/``repair``), which records ownership
and can roll back.
"""
from __future__ import annotations

from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from .core.config import ConfigStore
from .core.context import AppContext
from .core.errors import FoundationError, OwnershipConflict, SelectionError
from .core.paths import AppPaths
from .core.resources import ResourceCatalog

FLAGS = ("global", "mcp", "schedule", "shortcut")

_EXPLAIN = {
    "file": "Hook/kural dosyası (yalnızca Respected'ın bölümü yönetilir; diğer içerik korunur)",
    "mcp": "MCP sunucu kaydı 'respected-vault' (diğer sunucu kayıtları korunur)",
    "task": "Zamanlanmış sabah özeti görevi",
    "shortcut": "Masaüstü kısayolu",
    "registry": "Kayıt defteri girdisi",
}


class PlanError(Exception):
    def __init__(self, code, message, hint=""):
        super().__init__(message)
        self.code, self.message, self.hint = code, message, hint


def _desired(target):
    raw = target.get("desired")
    if not isinstance(raw, dict):
        raise PlanError("BAD_REQUEST", "target.desired must be an object.", "Pass {global, mcp, schedule, shortcut} booleans.")
    from .integrations.rendering import CLIENTS
    lists = {}
    for list_key in ("clients", "mcp_clients"):
        chosen = raw.get(list_key)
        if chosen is not None and (not isinstance(chosen, list) or any(c not in CLIENTS for c in chosen)):
            raise PlanError("BAD_REQUEST", f"desired.{list_key} must be a list of known AI client ids.", "Use: " + ", ".join(CLIENTS) + ".")
        if chosen is not None:
            lists[list_key] = sorted(chosen)
    unknown = sorted(set(raw) - set(FLAGS) - {"clients", "mcp_clients"})
    if unknown:
        raise PlanError("BAD_REQUEST", f"Unknown integration(s): {', '.join(unknown)}.", "Use: " + ", ".join(FLAGS) + ".")
    if any(not isinstance(value, bool) for key, value in raw.items() if key not in ("clients", "mcp_clients")):
        raise PlanError("BAD_REQUEST", "Integration flags must be booleans.", "Use true or false.")
    return {**{key: bool(raw.get(key, False)) for key in FLAGS}, **lists}


def _context(data_root, target):
    from .bootstrap import application_roots
    roots = application_roots()
    store = ConfigStore(data_root)
    config = store.read()
    raw = target.get("vault_path")
    identity = config.get("active_vault_id")
    entry = (config.get("vaults") or {}).get(identity)
    if raw is not None:
        if not isinstance(raw, str) or not Path(raw).is_absolute():
            raise PlanError("BAD_REQUEST", "target.vault_path must be an absolute path.", "Choose the vault folder.")
        vault = Path(raw)
        identity = next((key for key, row in (config.get("vaults") or {}).items() if Path(row["path"]).resolve() == vault.resolve()),
                        str(uuid5(NAMESPACE_URL, str(vault.resolve()))))
    elif entry:
        vault = Path(entry["path"])
    else:
        raise PlanError("BAD_REQUEST", "No vault is registered and no vault_path was given.", "Pass target.vault_path.")
    return roots, AppContext(AppPaths(roots.app_root, Path(data_root), vault, identity), config, ResourceCatalog())


def _describe(change):
    if change.before == change.after:
        action = "unchanged"
    elif change.before is None:
        action = "create"
    else:
        action = "modify"
    return {"kind": change.kind, "target": str(change.key), "action": action, "summary": _EXPLAIN.get(change.kind, change.kind),
            "size_after": len(change.after or b"")}


def _removals(ctx, backend, desired, data_root, planned=frozenset()):
    """Registrations Respected owns that the new choices switch off: exactly what the installer would restore."""
    from .installation.ownership import read_manifest
    manifest = Path(data_root) / "install-manifest.json"
    if not manifest.is_file():
        return []
    flag_by_kind = {"file": "global", "mcp": "mcp", "task": "schedule", "shortcut": "shortcut"}
    home = Path.home()
    name = "respected-morning-briefing-" + ctx.paths.vault_id
    schedule_paths = {str(home / ".config/systemd/user" / (name + suffix)) for suffix in (".service", ".timer")}
    schedule_paths.add(str(home / "Library/LaunchAgents" / (name + ".plist")))
    rows = []
    for prior in read_manifest(manifest).external:
        if prior.kind == "file" and Path(prior.key).is_relative_to(ctx.paths.vault_root):
            continue  # the vault's own hooks stay on independently of the optional global ones
        flag = "schedule" if prior.kind == "file" and prior.key in schedule_paths else flag_by_kind.get(prior.kind)
        dropped_client = (("clients" in desired or "mcp_clients" in desired) and flag in ("global", "mcp") and desired.get(flag, False)
                          and (prior.kind, str(prior.key)) not in planned)  # a client that is no longer selected
        if flag is None or (desired.get(flag, False) and not dropped_client):
            continue
        current = backend.read(prior.kind, prior.key)
        if prior.restored(current):
            continue
        from .installation.operations import _undo
        _undo(prior, current)  # raises OwnershipConflict only when our own entry was edited
        rows.append({"kind": prior.kind, "target": str(prior.key), "action": "restore", "summary": _EXPLAIN.get(prior.kind, prior.kind), "size_after": len(prior.before or b"")})
    return rows


def plan(data_root, target):
    from .installation.common import installed_profile
    from .integrations.backend import NativeBackend
    from .integrations.rendering import mcp_destinations, plan_integrations
    desired = _desired(target)
    try:
        roots, ctx = _context(data_root, target)
        profile_input = {key: target["profile"][key] for key in ("platform",) if isinstance(target.get("profile"), dict) and key in target["profile"]}
        profile = installed_profile(roots, profile_input)
        backend = NativeBackend(Path(data_root))
        discovered = [{"client_config": str(path), "present": path.exists()} for path in mcp_destinations(profile)]
        planned_changes = plan_integrations(ctx, profile, desired, backend)
        changes = _removals(ctx, backend, desired, data_root, {(c.kind, str(c.key)) for c in planned_changes}) + [_describe(change) for change in planned_changes]
    except PlanError:
        raise
    except OwnershipConflict as error:
        raise PlanError("LIFECYCLE_CONFLICT", f"Integration refused to protect existing configuration: {error}",
                        "Resolve or remove the conflicting entry, or leave this integration off.")
    except (FoundationError, SelectionError, ValueError, OSError) as error:
        raise PlanError("BAD_REQUEST", f"Integration plan failed: {error}", "Check the selected options.")
    from .integrations.rendering import detect_clients
    return {"desired": desired, "current": ConfigStore(Path(data_root)).read().get("integrations", {}),
            "launcher": list(profile.launcher), "discovered": discovered,
            "clients": [{"id": key, "detected": found} for key, found in detect_clients(profile).items()], "changes": changes,
            "writes_nothing": True, "external_effects": ["Windows Görev Zamanlayıcı"] if desired["schedule"] else []}
