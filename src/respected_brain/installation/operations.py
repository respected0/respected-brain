"""Common ownership and integration handling for maintenance operations."""
from dataclasses import replace
from pathlib import Path
from respected_brain.core.config import ConfigStore
from respected_brain.core.errors import OwnershipConflict
from respected_brain.core.paths import Roots
from respected_brain.integrations.backend import ExternalChange
from .common import ensure_linux_launcher, installed_profile, linux_launcher_path
from .ownership import safe_path, OwnedFile, OwnershipManifest, digest, manifest_document


def validate_manifest_roots(ctx, manifest):
    for item in manifest.files:
        safe_path(item.path)
        if item.role == "launcher":
            settings = ctx.config["vaults"][ctx.paths.vault_id].get("settings", {})
            profile = installed_profile(Roots(ctx.paths.app_root, ctx.paths.data_root, ctx.paths.vault_root), settings)
            if profile.platform != "posix" or item.path != linux_launcher_path(ctx, profile):
                raise OwnershipConflict(f"Ownership manifest exceeds launcher boundary: {item.path}")
            continue
        root = ctx.paths.app_root if item.role == "application" else ctx.paths.data_root
        if item.role not in ("application", "technical") or not item.path.is_relative_to(root) or item.path.is_relative_to(ctx.paths.vault_root):
            raise OwnershipConflict(f"Ownership manifest exceeds application/data boundary: {item.path}")


def undo_external(prior, current):
    """Our registration undone inside what the client/user has since written; refuses only when they changed our own entry."""
    try:
        return prior.undo(current)
    except ValueError:
        raise OwnershipConflict(f"User changed integration: {prior.kind}:{prior.key}") from None


def plan_connections(ctx, backend, previous):
    config = ConfigStore(ctx.paths.data_root).read()
    fresh = replace(ctx, config=config)
    desired = config["integrations"]
    disabled = []
    retained = []
    flag_by_kind = {"file": "global", "mcp": "mcp", "task": "schedule", "shortcut": "shortcut"}
    settings = config["vaults"][ctx.paths.vault_id].get("settings", {})
    home = Path(settings.get("user_home", str(Path.home())))
    name = "respected-morning-briefing-" + ctx.paths.vault_id
    schedule_paths = {str(home / ".config/systemd/user" / (name + suffix)) for suffix in (".service", ".timer")}
    schedule_paths.add(str(home / "Library/LaunchAgents" / (name + ".plist")))
    for prior in previous.external:
        # Local vault hooks remain enabled independently of optional global hooks.
        if prior.kind == "file" and Path(prior.key).is_relative_to(ctx.paths.vault_root):
            retained.append(prior)
            continue
        flag = "schedule" if prior.kind == "file" and prior.key in schedule_paths else flag_by_kind.get(prior.kind)
        if flag is not None and not desired.get(flag, False):
            current = backend.read(prior.kind, prior.key)
            if prior.restored(current):
                continue
            disabled.append(ExternalChange(prior.kind, prior.key, current, undo_external(prior, current)))
        else:
            retained.append(prior)
    if not any(desired.get(key, False) for key in ("global", "mcp", "schedule", "shortcut")):
        return tuple(disabled), tuple(retained)
    from respected_brain.integrations.rendering import plan_integrations
    roots = Roots(ctx.paths.app_root, ctx.paths.data_root, ctx.paths.vault_root)
    changes = plan_integrations(fresh, installed_profile(roots, settings), desired, backend)
    if "clients" in desired or "mcp_clients" in desired:  # a client that is no longer selected gets its previous registrations restored
        planned = {(change.kind, change.key) for change in changes}
        dropped = [prior for prior in retained if prior.kind in ("file", "mcp") and prior.key not in schedule_paths
                   and not Path(prior.key).is_relative_to(ctx.paths.vault_root) and (prior.kind, prior.key) not in planned]
        for prior in dropped:
            current = backend.read(prior.kind, prior.key)
            if prior.restored(current):
                continue
            disabled.append(ExternalChange(prior.kind, prior.key, current, undo_external(prior, current)))
        retained = [prior for prior in retained if prior not in dropped]
    owned = {(change.kind, change.key): change for change in retained}
    for change in changes:
        prior = owned.get((change.kind, change.key))
        owned[(change.kind, change.key)] = ExternalChange(change.kind, change.key, undo_external(prior, change.before) if prior else change.before, change.after)
    return (*disabled, *changes), tuple(owned.values())


def operation_manifest(ctx, files, external, *, previous=None):
    config_path = ctx.paths.data_root / "config.json"
    owned = {item.path: item for item in previous.files if item.role == "technical"} if previous is not None else {}
    owned.update({item.path: item for item in files})
    owned[config_path] = OwnedFile(config_path, digest(config_path), "technical")
    return OwnershipManifest(3, tuple(owned.values()), tuple(external))


def refresh_integrations(ctx, backend, tx, previous, profile):
    """Install the PATH launcher and apply the planned integration changes; returns (launchers, owned external rows)."""
    launchers = ensure_linux_launcher(ctx, profile, tx, previous)
    changes, external = plan_connections(ctx, backend, previous)
    for change in changes:
        tx.apply_external(change)
    return launchers, external


def write_manifest(ctx, tx, files, external, previous):
    tx.write_json(ctx.paths.data_root / "install-manifest.json",
                  manifest_document(operation_manifest(ctx, files, external, previous=previous)))
