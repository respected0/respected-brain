"""Repair selected product links without regenerating any user notes."""
from pathlib import Path

from respectedbrain.core.errors import FoundationError
from .ownership import digest, read_manifest
from .operations import validate_manifest_roots, refresh_integrations, write_manifest
from .transaction import Transaction, OperationResult, recover_transactions
from . import payload
from .common import installed_profile
from respectedbrain.core.paths import Roots


def repair(ctx, *, backend, package=None, require_provenance=None) -> OperationResult:
    tx = None
    try:
        if any(result.conflicts for result in recover_transactions(ctx.paths.data_root, backend)):
            return OperationResult(False, "", ("Unfinished rollback conflict",))
        with Transaction(ctx.paths.data_root, backend) as tx:
            previous = read_manifest(ctx.paths.data_root / "install-manifest.json")
            validate_manifest_roots(ctx, previous)
            roots = Roots(ctx.paths.app_root, ctx.paths.data_root, ctx.paths.vault_root)
            files = tuple(item for item in previous.files if item.role in ("application", "uninstaller"))
            if package is None:
                damaged = [
                    item.path for item in previous.files
                    if item.role == "application"
                    and (not item.path.is_file() or digest(item.path) != item.sha256)
                ]
                if damaged:
                    return OperationResult(
                        False,
                        "",
                        ("Verified repair package required to restore changed owned application files",),
                    )
                document = payload.validate_package(ctx.paths.app_root, require_provenance=require_provenance)
            else:
                from .operations import activate_package
                document, activated = activate_package(
                    roots,
                    Path(package).resolve(),
                    tx,
                    previous,
                    require_provenance=require_provenance,
                    repair_owned=True,
                )
                files = (*activated, *(item for item in files if item.role == "uninstaller"))
            settings = ctx.config["vaults"][ctx.paths.vault_id].get("settings", {})
            launchers, external = refresh_integrations(ctx, backend, tx, previous, installed_profile(roots, settings))
            write_manifest(ctx, tx, (*files, *launchers), external, previous)
            payload.validate_installed_health(ctx.paths.app_root, document, ctx.paths.data_root)
            return tx.commit()
    except (FoundationError, OSError, ValueError) as error:
        return OperationResult.failed(tx, error)
