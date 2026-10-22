"""Repair, settings changes and uninstall share one transaction and preserve notes and user changes."""
from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import patch

from respectedbrain.core.config import ConfigStore
from respectedbrain.installation.setup import setup
from respectedbrain.installation.repair import repair
from respectedbrain.installation.reconfigure import reconfigure
from respectedbrain.installation.uninstall import uninstall
from respectedbrain.core.paths import Roots
from respectedbrain.vault.registry import build_context
from respectedbrain.integrations.backend import ExternalChange
from respectedbrain.installation.ownership import OwnershipManifest, read_manifest, manifest_document
from tests.support.packages import seed_package
from tests.support.files import note_hashes, snapshot
from tests.support.fakes import Backend

OFF = {"integrations.global": False, "integrations.mcp": False, "integrations.schedule": False, "integrations.shortcut": False}


class FoundationOperationsTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.vault = self.root / "Türkçe 🧠 Vault"
        self.roots = Roots(self.root / "app", self.root / "data", self.vault)
        self.backend = Backend()
        self.health = patch("respectedbrain.installation.payload.validate_installed_health", return_value=None)
        self.health.start()
        self.addCleanup(self.health.stop)
        seed_package(self.roots.app_root)
        self.assertTrue(setup(self.roots, self.vault, values=OFF, backend=self.backend).success)
        store = ConfigStore(self.roots.data_root)
        store.update(lambda value: value["preferences"].update(summary_provider="codex"))
        self.ctx = build_context(self.roots, store, vault=self.vault, vault_id=None, env={})
        self.manifest_path = self.roots.data_root / "install-manifest.json"
        self.other = self.root / "İkinci Vault"
        self.other.mkdir()
        (self.other / "Core.md").write_bytes(b"other")

    def owned_external(self, change):
        manifest = read_manifest(self.manifest_path)
        self.manifest_path.write_text(json.dumps(manifest_document(OwnershipManifest(3, manifest.files, (change,)))), encoding="utf-8")

    def test_repair_after_the_installer_laid_down_a_new_version_records_it_and_keeps_everything_else(self):
        notes, other = note_hashes(self.vault), snapshot(self.other)
        config = ConfigStore(self.roots.data_root).read()
        seed_package(self.roots.app_root, content=b"MZ-new")
        result = repair(self.ctx, backend=self.backend)
        self.assertTrue(result.success, result.conflicts)
        from respectedbrain.installation.ownership import digest
        recorded = {item.path: item.sha256 for item in read_manifest(self.manifest_path).files}
        self.assertEqual(recorded[self.roots.app_root / "respectedbrain.exe"], digest(self.roots.app_root / "respectedbrain.exe"))
        self.assertEqual(ConfigStore(self.roots.data_root).read(), config)
        self.assertEqual((note_hashes(self.vault), snapshot(self.other)), (notes, other))

    def test_repair_refuses_a_damaged_program_and_leaves_it_to_the_installer(self):
        target = self.roots.app_root / "respectedbrain.exe"
        target.write_bytes(b"damaged")
        manifest = self.manifest_path.read_bytes()
        result = repair(self.ctx, backend=self.backend)
        self.assertFalse(result.success)
        self.assertIn("kurucuyu", " ".join(result.conflicts))
        self.assertEqual((target.read_bytes(), self.manifest_path.read_bytes()), (b"damaged", manifest))

    def test_maintenance_retains_migrated_technical_ownership_without_adopting_edits(self):
        from dataclasses import replace
        from respectedbrain.installation.ownership import OwnedFile, digest
        path = self.ctx.paths.state_dir / 'migration-receipts/fixture.json'
        path.parent.mkdir(parents=True)
        path.write_bytes(b'original-receipt')
        owned = OwnedFile(path, digest(path), 'technical')
        previous = read_manifest(self.manifest_path)
        self.manifest_path.write_text(json.dumps(manifest_document(replace(previous, files=previous.files + (owned,)))), encoding='utf-8')
        path.write_bytes(b'user-edited')
        for action in (lambda: repair(self.ctx, backend=self.backend),
                       lambda: setup(self.roots, self.vault, values=OFF, backend=self.backend)):
            result = action()
            self.assertTrue(result.success, result.conflicts)
            self.assertIn(owned, read_manifest(self.manifest_path).files)
            self.assertEqual(path.read_bytes(), b'user-edited')
        result = uninstall(self.ctx, backend=self.backend, purge_data=True)
        self.assertFalse(result.success)
        self.assertEqual(path.read_bytes(), b'user-edited')

    def test_health_timeout_fails_repair_without_touching_the_program(self):
        import subprocess
        before = snapshot(self.roots.app_root)
        self.health.stop()
        with patch('respectedbrain.installation.payload.subprocess.run', side_effect=subprocess.TimeoutExpired('fixture', 30)):
            result = repair(self.ctx, backend=self.backend)
        self.assertFalse(result.success)
        self.assertEqual(snapshot(self.roots.app_root), before)

    def test_corrupt_ownership_manifest_is_controlled_failure(self):
        before = snapshot(self.roots.app_root)
        for document in ([], {'schema_version': 3}, {'schema_version': 3, 'files': [None], 'external': []}):
            with self.subTest(document=document):
                self.manifest_path.write_text(json.dumps(document), encoding='utf-8')
                self.assertFalse(repair(self.ctx, backend=self.backend).success)
                self.assertEqual(snapshot(self.roots.app_root), before)

    def test_distribution_member_alias_is_rejected(self):
        from respectedbrain.installation.payload import validate_package
        from respectedbrain.core.errors import OwnershipConflict
        path = self.roots.app_root / 'distribution.json'
        document = json.loads(path.read_text())
        document['files']['./respectedbrain.exe'] = document['files']['respectedbrain.exe']
        path.write_text(json.dumps(document), encoding='utf-8')
        with self.assertRaises(OwnershipConflict):
            validate_package(self.roots.app_root)

    def test_failed_settings_change_restores_config_and_external_records(self):
        config = (self.roots.data_root / "config.json").read_bytes()
        manifest = self.manifest_path.read_bytes()

        def enable(document):
            document["integrations"]["global"] = True
            document["vaults"][self.ctx.paths.vault_id]["settings"]["COMPANION"] = "Jarvis"
        with patch.object(self.backend, "apply", side_effect=OSError("client file locked")), \
                patch("respectedbrain.bootstrap.application_roots", return_value=self.roots):
            result = reconfigure(self.roots.data_root, enable, backend=self.backend)
        self.assertFalse(result.success)
        self.assertEqual(((self.roots.data_root / "config.json").read_bytes(), self.manifest_path.read_bytes()), (config, manifest))

    def test_uninstall_keeps_the_program_and_settings_and_drops_the_install_record(self):
        before = note_hashes(self.vault)
        program = snapshot(self.roots.app_root)
        result = uninstall(self.ctx, backend=self.backend, purge_data=False)
        self.assertTrue(result.success, result.conflicts)
        self.assertEqual(snapshot(self.roots.app_root), program)
        self.assertTrue((self.roots.data_root / "config.json").exists())
        self.assertFalse(self.manifest_path.exists())
        self.assertEqual(note_hashes(self.vault), before)

    def test_owned_record_changed_by_user_is_retained(self):
        self.owned_external(ExternalChange("mcp", "test", b"old", b"owned"))
        self.backend.records[("mcp", "test")] = b"user"
        result = uninstall(self.ctx, backend=self.backend)
        self.assertFalse(result.success)
        self.assertEqual(self.backend.read("mcp", "test"), b"user")
        self.assertIn("mcp:test", result.conflicts)

    def test_disabled_owned_integrations_restore_original_records(self):
        change = ExternalChange("mcp", str(self.root / "home/.cursor/mcp.json"), b"user-original", b"managed")
        self.owned_external(change)
        self.backend.records[(change.kind, change.key)] = change.after
        result = repair(self.ctx, backend=self.backend)
        self.assertTrue(result.success, result.conflicts)
        self.assertEqual(self.backend.read(change.kind, change.key), change.before)
        self.assertEqual(read_manifest(self.manifest_path).external, ())

    def test_disabling_user_changed_integration_is_a_conflict(self):
        change = ExternalChange("mcp", str(self.root / "mcp.json"), None, b"managed")
        self.owned_external(change)
        self.backend.records[(change.kind, change.key)] = b"edited"
        result = repair(self.ctx, backend=self.backend)
        self.assertFalse(result.success)
        self.assertEqual(self.backend.read(change.kind, change.key), b"edited")


if __name__ == "__main__":
    unittest.main()
