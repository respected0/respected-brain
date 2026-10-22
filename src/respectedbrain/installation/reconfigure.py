"""A settings change that reaches outside the data folder: config and owned integrations change in one transaction."""
from dataclasses import replace
from pathlib import Path

from respectedbrain.core.config import ConfigStore
from respectedbrain.core.errors import FoundationError, SelectionError
from respectedbrain.core.paths import Roots
from respectedbrain.integrations.backend import NativeBackend
from .common import installation_context, installed_profile
from .operations import refresh_integrations, validate_manifest_roots, write_manifest
from .ownership import read_manifest
from .transaction import OperationResult, Transaction, recover_transactions


def reconfigure(data_root: Path, mutator, *, backend=None) -> OperationResult:
    from respectedbrain.bootstrap import application_roots
    backend = backend or NativeBackend(data_root)
    tx = None
    try:
        if any(result.conflicts for result in recover_transactions(data_root, backend)):
            return OperationResult(False, "", ("Unfinished rollback conflict",))
        store = ConfigStore(data_root)
        before = store.read()
        identity = before.get("active_vault_id")
        if identity not in before["vaults"]:
            raise SelectionError("No registered vault")
        vault = Path(before["vaults"][identity]["path"])
        roots = Roots(application_roots().app_root, data_root, vault)
        with Transaction(data_root, backend) as tx:
            previous = read_manifest(data_root / "install-manifest.json")
            ctx = installation_context(roots, vault, identity, before)
            validate_manifest_roots(ctx, previous)
            ctx = replace(ctx, config=store.update(mutator, writer=tx.write_json))
            settings = ctx.config["vaults"][identity].get("settings", {})
            launchers, external = refresh_integrations(ctx, backend, tx, previous, installed_profile(roots, settings))
            files = tuple(item for item in previous.files if item.role == "application")
            write_manifest(ctx, tx, (*files, *launchers), external, previous)
            return tx.commit()
    except (FoundationError, OSError, ValueError) as error:
        return OperationResult.failed(tx, error)
