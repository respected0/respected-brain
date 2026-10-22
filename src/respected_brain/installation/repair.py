"""Repair: re-verify the program the installer laid down and restore the product's own records and integrations.

Run by the installer after it has written (new or the same) program files, so the recorded hashes follow
distribution.json, not the previous record. Damaged program files are the installer's to replace.
"""
from respected_brain.core.errors import FoundationError, OwnershipConflict
from respected_brain.core.paths import Roots
from respected_brain.integrations.plugin import install_plugins
from .common import installed_profile
from .operations import validate_manifest_roots, refresh_integrations, write_manifest
from .ownership import read_manifest
from .setup import application_files
from .transaction import Transaction, OperationResult, recover_transactions
from . import payload


def repair(ctx, *, backend) -> OperationResult:
    tx = None
    try:
        if any(result.conflicts for result in recover_transactions(ctx.paths.data_root, backend)):
            return OperationResult(False, "", ("Unfinished rollback conflict",))
        try:
            document = payload.validate_package(ctx.paths.app_root)
        except OwnershipConflict as error:
            return OperationResult(False, "", (f"Program dosyaları bozuk; kurucuyu yeniden çalıştırın: {error}",))
        with Transaction(ctx.paths.data_root, backend) as tx:
            previous = read_manifest(ctx.paths.data_root / "install-manifest.json")
            validate_manifest_roots(ctx, previous)
            roots = Roots(ctx.paths.app_root, ctx.paths.data_root, ctx.paths.vault_root)
            settings = ctx.config["vaults"][ctx.paths.vault_id].get("settings", {})
            profile = installed_profile(roots, settings)
            launchers, external = refresh_integrations(ctx, backend, tx, previous, profile)
            write_manifest(ctx, tx, (*application_files(ctx.paths.app_root, document), *launchers), external, previous)
            payload.validate_installed_health(ctx.paths.app_root, document, ctx.paths.data_root)
            result = tx.commit()
            if result.success:
                install_plugins(ctx, profile, ctx.config["integrations"])
            return result
    except (FoundationError, OSError, ValueError) as error:
        return OperationResult.failed(tx, error)
