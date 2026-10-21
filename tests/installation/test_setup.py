"""Setup creates a pure vault once and never templates over registered notes."""
from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import patch

from respectedbrain.core.paths import Roots
from respectedbrain.core.config import ConfigStore
from respectedbrain.installation.setup import setup
from respectedbrain.installation.ownership import read_manifest
from tests.support.packages import seed_package
from tests.support.files import snapshot, note_hashes
from tests.support.fakes import Backend


class FoundationSetupTest(unittest.TestCase):
    def test_repeated_setup_refuses_manifest_file_outside_program_root(self):
        from dataclasses import replace
        from respectedbrain.installation.ownership import OwnedFile, digest, manifest_document
        self.assertTrue(self.install().success)
        sentinel = self.root / 'human-note.md'
        sentinel.write_bytes(b'user')
        manifest_path = self.roots.data_root / 'install-manifest.json'
        manifest = read_manifest(manifest_path)
        manifest_path.write_text(json.dumps(manifest_document(replace(manifest, files=manifest.files + (OwnedFile(sentinel, digest(sentinel), 'application'),)))), encoding='utf-8')
        before = snapshot(self.roots.app_root)
        result = self.install()
        self.assertFalse(result.success)
        self.assertEqual(sentinel.read_bytes(), b'user')
        self.assertEqual(snapshot(self.roots.app_root), before)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        (self.root / "home").mkdir()
        self.vault = self.root / "Türkçe 🧠 Vault"
        self.roots = Roots(self.root / "app", self.root / "data", self.vault)
        self.package = seed_package(self.root / "package")
        self.backend = Backend()
        self.desired = dict.fromkeys(("global", "mcp", "schedule", "shortcut"), False)
        self.health = patch("respectedbrain.installation.payload.validate_installed_health", return_value=None)
        self.health.start()
        self.addCleanup(self.health.stop)

    def install(self, **kwargs):
        kwargs.setdefault("require_provenance", False)
        return setup(self.roots, self.vault, profile={"OS_NAME": "RespectedOS", "USER_NAME": "Ada", "USER_BIO": "Test", "COMPANION": "Atlas", "platform": "windows-native", "user_home": str(self.root / "home")}, desired=self.desired, backend=self.backend, package=kwargs.pop("package", self.package), **kwargs)

    def action(self, *, profile=None, desired=None):
        values = {"OS_NAME": "AdaOS", "USER_NAME": "Ada Lovelace", "USER_BIO": "Algoritma Mimarı", "COMPANION": "Babbage",
                  "platform": "windows-native", "user_home": str(self.root / "home"), **(profile or {})}
        return setup(self.roots, self.vault, profile=values, desired=self.desired if desired is None else desired,
                     backend=self.backend, package=self.package, require_provenance=False)

    def global_hooks(self):
        # hooks are global only (vault keeps notes + .obsidian), so they are read from the fake home
        self.assertFalse((self.vault / ".claude").exists())
        return (self.root / "home/.claude/settings.json").read_text(encoding="utf-8")

    def test_fresh_setup_is_pure_vault(self):
        result = self.install()
        self.assertTrue(result.success, result.conflicts)
        marker = json.loads((self.vault / ".respected.json").read_text())
        config = ConfigStore(self.roots.data_root).read()
        self.assertEqual(marker["schema_version"], 3)
        self.assertEqual(config["active_vault_id"], marker["vault_id"])
        self.assertFalse(config["integrations"]["schedule"])
        self.assertFalse((self.vault / "unins000.exe").exists())
        self.assertFalse(any(self.vault.rglob("*.db")))
        self.assertIn("Atlas", (self.vault / "🔮 850-Companion/Core.md").read_text(encoding="utf-8"))
        self.assertNotIn("{{", (self.vault / "🔮 850-Companion/Core.md").read_text(encoding="utf-8"))

    def test_nonempty_unregistered_target_is_untouched(self):
        self.vault.mkdir()
        (self.vault / "keep.py").write_bytes(b"user")
        before = snapshot(self.root)
        result = self.install()
        self.assertFalse(result.success)
        self.assertEqual(snapshot(self.root), before)

    def test_manifest_does_not_own_user_notes_and_repeat_preserves_edits(self):
        self.assertTrue(self.install().success)
        core = self.vault / "🔮 850-Companion/Core.md"
        core.write_text("# Kullanıcı\nÖzel kimlik.", encoding="utf-8")
        before = note_hashes(self.vault)
        self.assertTrue(self.install(package=None).success)
        self.assertEqual(note_hashes(self.vault), before)
        manifest = read_manifest(self.roots.data_root / "install-manifest.json")
        self.assertTrue(manifest.files)
        self.assertFalse(any(item.path.is_relative_to(self.vault) or item.role == "note" for item in manifest.files))

    def test_missing_or_changed_application_is_not_success(self):
        self.assertFalse(self.install(package=None).success)
        self.assertTrue(self.install().success)
        (self.roots.app_root / "respectedbrain.exe").write_bytes(b"changed")
        before = note_hashes(self.vault)
        self.assertFalse(self.install(package=None).success)
        self.assertEqual(note_hashes(self.vault), before)

    def test_busy_writer_blocks_activation(self):
        self.backend.busy = True
        before = snapshot(self.roots.app_root)
        result = self.install()
        self.assertFalse(result.success)
        self.assertEqual(snapshot(self.roots.app_root), before)
        self.assertFalse(self.vault.exists())

    def test_profile_provider_is_saved_and_repeat_preserves_preference(self):
        result = setup(self.roots, self.vault, profile={"summary_provider": "codex"}, desired=self.desired,
                       backend=self.backend, package=self.package, require_provenance=False)
        self.assertTrue(result.success, result.conflicts)
        self.assertEqual(ConfigStore(self.roots.data_root).read()["preferences"]["summary_provider"], "codex")
        self.assertTrue(self.install(package=None).success)
        self.assertEqual(ConfigStore(self.roots.data_root).read()["preferences"]["summary_provider"], "codex")

    def test_fresh_native_install_renders_global_hooks_for_final_registered_uuid(self):
        from respectedbrain.integrations.backend import NativeBackend
        self.backend = NativeBackend(self.roots.data_root)
        self.assertTrue(self.action(desired={**self.desired,"global":True}).success)
        identity=json.loads((self.vault / ".respected.json").read_text())["vault_id"]
        content=self.global_hooks()
        self.assertIn(identity,content)
        self.assertIn(str(self.roots.app_root / "respectedbrain.exe").replace("\\","\\\\"),content)
        self.assertNotIn(".respected-stage",content)

    def test_reinstall_preserves_user_note_and_project_config_bytes(self):
        self.assertTrue(self.action().success)
        path=self.vault / "knowledge/human-note.md"
        path.write_bytes("İnsan notu.\n".encode())
        settings=self.vault / ".claude/settings.json"
        settings.parent.mkdir()
        settings.write_bytes(b'{"myProjectSetting":true}')
        before=snapshot(self.vault)
        self.assertTrue(self.action().success)
        self.assertEqual(snapshot(self.vault),before)

    def test_reinstall_applies_requested_vault_shortcut(self):
        self.assertTrue(self.action().success)
        result=self.action(desired={**self.desired,"shortcut":True})
        self.assertTrue(result.success,result.conflicts)
        rows=[value for (kind,key),value in self.backend.records.items() if kind=="shortcut"]
        self.assertEqual(len(rows),1)
        self.assertIn("open --vault-id",json.loads(rows[0])["arguments"])

    def test_requested_global_failure_is_reported_and_existing_notes_retained(self):
        self.assertTrue(self.action().success)
        before=snapshot(self.vault)
        with patch.object(self.backend,"apply",side_effect=OSError("global failure")):
            result=self.action(desired={**self.desired,"global":True})
        self.assertFalse(result.success)
        self.assertEqual(snapshot(self.vault),before)

    def test_native_install_persists_only_stable_application_launcher(self):
        from respectedbrain.integrations.backend import NativeBackend
        self.backend = NativeBackend(self.roots.data_root)
        self.assertTrue(self.action(desired={**self.desired,"global":True}).success)
        content=self.global_hooks()
        self.assertIn("respectedbrain.exe",content)
        self.assertNotIn("python",content)
        self.assertNotIn(".py",content)

    def test_integration_failure_rolls_back_partial_fresh_install(self):
        with patch.object(self.backend,"apply",side_effect=OSError("integration failed")):
            result=self.action(desired={**self.desired,"global":True})
        self.assertFalse(result.success)
        self.assertFalse(self.vault.exists())
        self.assertFalse((self.roots.app_root / "respectedbrain.exe").exists())

    def test_custom_priority_is_saved_in_data_config(self):
        self.assertTrue(self.action(profile={"provider_priority":["antigravity","codex"]}).success)
        self.assertEqual(ConfigStore(self.roots.data_root).read()["preferences"]["provider_priority"],["antigravity","codex"])

    def test_single_provider_lock_retains_fail_fast_setting(self):
        self.assertTrue(self.action(profile={"summary_provider":"codex","provider_fallback":False}).success)
        preferences=ConfigStore(self.roots.data_root).read()["preferences"]
        self.assertEqual(preferences["summary_provider"],"codex")
        self.assertFalse(preferences["provider_fallback"])

    def test_mcp_registration_uses_installed_launcher_and_uuid(self):
        result=self.action(desired={**self.desired,"mcp":True})
        self.assertTrue(result.success,result.conflicts)
        records=[json.loads(value) for (kind,key),value in self.backend.records.items() if kind=="mcp" and value and "mcpServers" in json.loads(value)]
        self.assertTrue(records)
        for record in records:
            command=record["mcpServers"]["respected-vault"]
            self.assertEqual(command["command"],str(self.roots.app_root / "respectedbrain.exe"))
            self.assertEqual(command["args"][0],"mcp")
            self.assertIn("--vault-id",command["args"])

    def test_vault_gets_no_local_hook_folders_and_notes_survive_maintenance(self):
        from respectedbrain.integrations.backend import NativeBackend
        from respectedbrain.installation.update import update
        from respectedbrain.installation.repair import repair
        from respectedbrain.installation.uninstall import uninstall
        from respectedbrain.vault.registry import build_context
        names = ('.agents/hooks.json', '.claude/settings.json', '.codex/hooks.json',
                 '.cursor/hooks.json', '.gemini/settings.json')
        for purge in (True, False):
            with self.subTest(purge=purge):
                root = self.root / str(purge)
                home = root / 'home'
                home.mkdir(parents=True)
                roots = Roots(root / 'app', root / 'data', root / 'vault')
                backend = NativeBackend(roots.data_root)
                result = setup(roots, roots.default_vault, profile={'platform': 'windows-native',
                    'user_home': str(home)}, desired=self.desired, backend=backend,
                    package=self.package, require_provenance=False)
                self.assertTrue(result.success, result.conflicts)
                ctx = build_context(roots, ConfigStore(roots.data_root), vault=roots.default_vault, vault_id=None, env={})
                notes = note_hashes(roots.default_vault)
                self.assertTrue(all(not (roots.default_vault / name).exists() for name in names))
                for operation in (lambda: update(ctx, package=self.package, backend=backend, require_provenance=False),
                                  lambda: repair(ctx, backend=backend, require_provenance=False)):
                    result = operation()
                    self.assertTrue(result.success, result.conflicts)
                    self.assertTrue(all(not (roots.default_vault / name).exists() for name in names))
                result = uninstall(ctx, backend=backend, purge_data=purge)
                self.assertTrue(result.success, result.conflicts)
                self.assertEqual(note_hashes(roots.default_vault), notes)

    def test_install_rolls_back_when_install_health_fails(self):
        from respectedbrain.integrations.backend import NativeBackend
        self.backend = NativeBackend(self.roots.data_root)
        with patch('respectedbrain.installation.payload.validate_installed_health', side_effect=OSError('health failure')):
            result = self.install()
        self.assertFalse(result.success)
        self.assertEqual(result.conflicts, ('health failure',))
        self.assertFalse(self.vault.exists())
