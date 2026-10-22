"""Remove the integrations and records the product owns; with purge also its data. Never notes, never the program:
the installer that laid the program files down removes them."""
from pathlib import Path

from respectedbrain.core.errors import FoundationError
from respectedbrain.integrations.backend import ExternalChange
from .ownership import read_manifest, prove_ownership
from .operations import validate_manifest_roots
from .transaction import Transaction, OperationResult, recover_transactions, scrub_committed_journals


_CLIENT_ROOTS = (".agents", ".claude", ".codex", ".cursor", ".gemini", ".codeium")


def prune_empty_client_dirs(files) -> None:
    """Remove the empty folders our removed skills/rules/hooks leave inside AI-client folders.

    Only directories strictly below a client folder (.claude, .codex, ...) are pruned, never the client folder itself,
    except `.agents` which only we create; anything non-empty is left alone."""
    for file in files:
        parts = Path(file).parts
        index = next((i for i, part in enumerate(parts) if part in _CLIENT_ROOTS), None)
        if index is None:
            continue
        floor = index if parts[index] == ".agents" else index + 1
        directory = Path(*parts[:-1])
        while len(directory.parts) > floor:
            try:
                directory.rmdir()
            except OSError:
                break
            directory = directory.parent


def uninstall(ctx, *, backend, purge_data=False) -> OperationResult:
    tx = None
    try:
        if any(result.conflicts for result in recover_transactions(ctx.paths.data_root, backend)):
            return OperationResult(False, "", ("Unfinished rollback conflict",))
        conflicts = []
        manifest_path = ctx.paths.data_root / "install-manifest.json"
        manifest_before = manifest_path.read_bytes()
        with Transaction(ctx.paths.data_root, backend) as tx:
            manifest = read_manifest(manifest_path)
            validate_manifest_roots(ctx, manifest)
            for change in reversed(manifest.external):
                current = backend.read(change.kind, change.key)
                if change.restored(current):
                    continue
                try:
                    restored = change.undo(current)
                except ValueError:
                    conflicts.append(change.kind + ":" + change.key)
                    continue
                tx.apply_external(ExternalChange(change.kind, change.key, current, restored))
            for item in manifest.files:
                if item.role == "application" or item.role == "technical" and not purge_data or not item.path.exists():
                    continue
                if not prove_ownership(item.path, manifest):
                    conflicts.append(str(item.path))
                    continue
                tx.remove(item.path, expected_hash=item.sha256)
            result = tx.commit()
            prune_empty_client_dirs(change.key for change in manifest.external if change.kind == "file")
            scrub_committed_journals(ctx.paths.data_root)
            if not conflicts:  # the install record always goes with the program; settings stay unless purged
                if manifest_path.is_file() and manifest_path.read_bytes() == manifest_before:
                    manifest_path.unlink()
                else:
                    conflicts.append(str(manifest_path))
                    return OperationResult(False, result.tx_id, tuple(conflicts))
            # Unknown files and backup journals are deliberately retained.
            return OperationResult(not conflicts, result.tx_id, tuple(conflicts))
    except (FoundationError, OSError, ValueError) as error:
        return OperationResult.failed(tx, error)
