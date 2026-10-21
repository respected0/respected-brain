"""Verified package activation with rollback; user notes are outside the payload."""
from respectedbrain.core.config import ConfigStore
from respectedbrain.core.errors import FoundationError
from respectedbrain.core.paths import Roots
from .ownership import read_manifest
from .operations import validate_manifest_roots, activate_package, refresh_integrations, write_manifest
from .transaction import Transaction, OperationResult, recover_transactions
from . import payload
from .common import installed_profile


def update(ctx, *, package, backend, require_provenance=None) -> OperationResult:
    tx = None
    try:
        payload.validate_package(package, require_provenance=require_provenance)
        if any(result.conflicts for result in recover_transactions(ctx.paths.data_root, backend)):
            return OperationResult(False, "", ("Unfinished rollback conflict",))
        with Transaction(ctx.paths.data_root, backend) as tx:
            previous = read_manifest(ctx.paths.data_root / "install-manifest.json")
            validate_manifest_roots(ctx, previous)
            tx.checkpoint("backup")
            for item in previous.files:
                if item.path.exists():
                    tx.backup(item.path)
            tx.checkpoint("stage")
            roots = Roots(ctx.paths.app_root, ctx.paths.data_root, ctx.paths.vault_root)
            document, files = activate_package(roots, package, tx, previous, require_provenance=require_provenance)
            tx.checkpoint("activate")
            # Read the latest preferences under the config lock; never copy defaults over them.
            ConfigStore(ctx.paths.data_root).update(lambda value: None, writer=tx.write_json)
            tx.checkpoint("config")
            settings = ctx.config["vaults"][ctx.paths.vault_id].get("settings", {})
            launchers, external = refresh_integrations(ctx, backend, tx, previous, installed_profile(roots, settings))
            tx.checkpoint("integrations")
            write_manifest(ctx, tx, (*files, *launchers), external, previous)
            tx.checkpoint("health")
            payload.validate_package(ctx.paths.app_root, require_provenance=require_provenance)
            payload.validate_installed_health(ctx.paths.app_root, document, ctx.paths.data_root)
            tx.checkpoint("cleanup")
            return tx.commit()
    except (FoundationError, OSError, ValueError) as error:
        return OperationResult.failed(tx, error)
