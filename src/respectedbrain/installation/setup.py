"""First-time setup after the installer has laid down the program: vault, configuration, integrations, records.

The program files belong to the installer; setup verifies them against distribution.json and records their hashes
so repair can tell a damaged installation. Notes are created once and never touched again.
"""
from __future__ import annotations
from datetime import date
from pathlib import Path
import stat
from typing import Mapping

from respectedbrain import settings as product_settings
from respectedbrain.core.config import ConfigStore
from respectedbrain.core.errors import FoundationError, OwnershipConflict
from respectedbrain.core.paths import Roots
from respectedbrain.core.resources import ResourceCatalog
from respectedbrain.vault.registry import VaultRegistry
from .common import installed_profile, installation_context
from .ownership import OwnedFile, OwnershipManifest, digest, read_manifest, safe_path
from .transaction import Transaction, OperationResult, recover_transactions
from . import payload


def application_files(app_root: Path, document) -> tuple[OwnedFile, ...]:
    return tuple(OwnedFile(app_root / name, digest(app_root / name), "application", stat.S_IMODE((app_root / name).stat().st_mode))
                 for name in payload.package_members(document))


def setup(roots: Roots, vault: Path, *, values: Mapping[str, object], backend, platform: str | None = None,
          home: Path | None = None) -> OperationResult:
    tx = None
    try:
        safe_path(vault)
        if vault.is_relative_to(roots.app_root) or roots.app_root.is_relative_to(vault) or vault.is_relative_to(roots.data_root) or roots.data_root.is_relative_to(vault):
            raise OwnershipConflict("Vault, program and data roots must be separate")
        errors = product_settings.field_errors(dict(values))
        if errors:
            raise ValueError("; ".join(error["message"] for error in errors))
        store = ConfigStore(roots.data_root)
        config = store.read()
        registered = next((identity for identity, entry in config["vaults"].items() if Path(entry["path"]).resolve() == vault.resolve()), None)
        # a registration whose folder was deleted or moved is stale: the vault is created again, the old entry dropped
        stale = [registered] if registered is not None and not vault.is_dir() else []
        if stale:
            registered = None
        if registered is None and vault.exists() and any(vault.iterdir()):
            return OperationResult(False, "", ("Nonempty target is not registered; use vault register",))
        if registered is not None:
            VaultRegistry(store).select(vault=vault, vault_id=None, env={})
        document = payload.validate_package(roots.app_root)
        recovery = recover_transactions(roots.data_root, backend)
        if any(item.conflicts for item in recovery):
            raise OwnershipConflict("Unfinished operation has rollback conflicts")
        profile = product_settings.profile_of(values)
        with Transaction(roots.data_root, backend) as tx:
            tx.checkpoint("backup")
            manifest_path = roots.data_root / "install-manifest.json"
            previous = read_manifest(manifest_path) if manifest_path.is_file() else OwnershipManifest(3, (), ())
            if previous.files:
                from .operations import validate_manifest_roots
                prior_identity = registered or config["active_vault_id"]
                if prior_identity is None:
                    raise OwnershipConflict("Existing ownership requires a registered vault identity")
                validate_manifest_roots(installation_context(roots, vault, prior_identity, config), previous)
            if stale:
                def drop_stale(value):
                    for identity in stale:
                        value["vaults"].pop(identity, None)
                    if value.get("active_vault_id") in stale:
                        value["active_vault_id"] = None
                store.update(drop_stale, writer=tx.write_json)
            if registered is None:
                if vault.exists() and any(vault.iterdir()):
                    raise OwnershipConflict("Vault changed during installation")
                template = {"TODAY": date.today().isoformat(), "VAULT_PATH": str(vault), "OS_NAME": vault.name,
                            "USER_NAME": Path.home().name, "USER_BIO": "", "COMPANION": "Companion", **profile}
                with ResourceCatalog().materialize("vault-template") as stage:
                    for file in stage.rglob("*"):
                        if file.is_file() and (file.suffix.lower() in (".md", ".json", ".mdc", ".txt", ".yaml", ".yml") or file.name.startswith(".")):
                            text = file.read_text(encoding="utf-8")
                            for key, value in template.items():
                                text = text.replace("{{" + key + "}}", str(value))
                            file.write_text(text, encoding="utf-8")
                    tx.replace(stage, vault)
            identity = VaultRegistry(store).register(vault, writer=tx.write_json)
            tx.checkpoint("config")
            resolved_profile = installed_profile(roots, {key: str(value) for key, value in (("platform", platform), ("user_home", home)) if value})
            def edit(value):
                value["vaults"][identity]["settings"].setdefault("OS_NAME", vault.name)
                value["vaults"][identity]["settings"].setdefault("platform", resolved_profile.platform)
                value["vaults"][identity]["settings"].setdefault("user_home", str(resolved_profile.user_home))
                product_settings.write(value, dict(values))
            config = store.update(edit, writer=tx.write_json)
            ctx = installation_context(roots, vault, identity, config)
            # Hooks are global only (home-level); the vault keeps just its notes and .obsidian (no .claude/.cursor/.agents/...).
            from .operations import refresh_integrations, write_manifest
            launchers, external = refresh_integrations(ctx, backend, tx, previous, installed_profile(roots, config["vaults"][identity]["settings"]))
            tx.checkpoint("integrations")
            owned = application_files(roots.app_root, document) + (OwnedFile(store.path, digest(store.path), "technical"),) + launchers
            write_manifest(ctx, tx, owned, external, previous)
            tx.checkpoint("health")
            payload.validate_installed_health(roots.app_root, document, roots.data_root)
            tx.checkpoint("cleanup")
            return tx.commit()
    except (FoundationError, OSError, ValueError) as error:
        return OperationResult.failed(tx, error)
