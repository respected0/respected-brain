"""Setup records the program the installer laid down, creates a pure vault once and never templates over notes."""
from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import patch

from respected_brain.core.paths import Roots
from respected_brain.core.config import ConfigStore
from respected_brain.installation.setup import setup
from respected_brain.installation.ownership import read_manifest
from tests.support.packages import seed_package
from tests.support.files import snapshot, note_hashes
from tests.support.fakes import Backend

OFF = {"integrations.global": False, "integrations.mcp": False, "integrations.schedule": False, "integrations.shortcut": False}


class FoundationSetupTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        (self.root / "home").mkdir()
        self.vault = self.root / "Türkçe 🧠 Vault"
        self.roots = Roots(self.root / "app", self.root / "data", self.vault)
        seed_package(self.roots.app_root)  # what the installer lays down
        self.backend = Backend()
        self.health = patch("respected_brain.installation.payload.validate_installed_health", return_value=None)
        self.health.start()
        self.addCleanup(self.health.stop)

    def install(self, roots=None, **values):
        roots = roots or self.roots
        return setup(roots, roots.default_vault if roots is not self.roots else self.vault,
                     values={"user_name": "Ada", "user_bio": "Test", "assistant_name": "Atlas", **OFF, **values},
                     backend=self.backend, platform="windows-native", home=self.root / "home")

    def global_hooks(self):
        # hooks are global only (vault keeps notes + .obsidian), so they are read from the fake home
        self.assertFalse((self.vault / ".claude").exists())
        return "".join(path.read_text(encoding="utf-8") for path in (self.root / "data/vaults").glob("*/plugin/plugin/hooks/claude.json"))

    def test_fresh_setup_is_pure_vault(self):
        result = self.install()
        self.assertTrue(result.success, result.conflicts)
        marker = json.loads((self.vault / ".respected.json").read_text())
        config = ConfigStore(self.roots.data_root).read()
        self.assertEqual(marker["schema_version"], 3)
        self.assertEqual(config["active_vault_id"], marker["vault_id"])
        self.assertFalse(config["integrations"]["schedule"])
        self.assertEqual(config["vaults"][marker["vault_id"]]["settings"]["USER_NAME"], "Ada")
        self.assertFalse(any(self.vault.rglob("*.db")))
        self.assertIn("Atlas", (self.vault / "🔮 850-Companion/Core.md").read_text(encoding="utf-8"))
        self.assertNotIn("{{", (self.vault / "🔮 850-Companion/Core.md").read_text(encoding="utf-8"))

    def test_setup_recreates_a_registered_vault_whose_folder_is_gone(self):
        import shutil
        self.assertTrue(self.install().success)
        shutil.rmtree(self.vault)
        result = self.install()
        self.assertTrue(result.success, result)
        config = ConfigStore(self.roots.data_root).read()
        self.assertEqual([Path(entry["path"]).resolve() for entry in config["vaults"].values()].count(self.vault.resolve()), 1)
        self.assertTrue((self.vault / ".respected.json").is_file())

    def test_repeated_setup_refuses_manifest_file_outside_program_root(self):
        from dataclasses import replace
        from respected_brain.installation.ownership import OwnedFile, digest, manifest_document
        self.assertTrue(self.install().success)
        sentinel = self.root / 'human-note.md'
        sentinel.write_bytes(b'user')
        manifest_path = self.roots.data_root / 'install-manifest.json'
        manifest = read_manifest(manifest_path)
        manifest_path.write_text(json.dumps(manifest_document(replace(manifest, files=manifest.files + (OwnedFile(sentinel, digest(sentinel), 'application'),)))), encoding='utf-8')
        before = snapshot(self.roots.app_root)
        self.assertFalse(self.install().success)
        self.assertEqual(sentinel.read_bytes(), b'user')
        self.assertEqual(snapshot(self.roots.app_root), before)

    def test_nonempty_unregistered_target_is_untouched(self):
        self.vault.mkdir()
        (self.vault / "keep.py").write_bytes(b"user")
        before = snapshot(self.root)
        self.assertFalse(self.install().success)
        self.assertEqual(snapshot(self.root), before)

    def test_manifest_records_the_program_but_not_user_notes_and_repeat_preserves_edits(self):
        self.assertTrue(self.install().success)
        core = self.vault / "🔮 850-Companion/Core.md"
        core.write_text("# Kullanıcı\nÖzel kimlik.", encoding="utf-8")
        before = note_hashes(self.vault)
        self.assertTrue(self.install().success)
        self.assertEqual(note_hashes(self.vault), before)
        manifest = read_manifest(self.roots.data_root / "install-manifest.json")
        self.assertIn(self.roots.app_root / "respected-brain.exe", {item.path for item in manifest.files if item.role == "application"})
        self.assertFalse(any(item.path.is_relative_to(self.vault) for item in manifest.files))

    def test_missing_or_changed_program_is_not_success(self):
        (self.roots.app_root / "respected-brain.exe").write_bytes(b"changed")
        self.assertFalse(self.install().success)
        self.assertFalse(self.vault.exists())
        (self.roots.app_root / "respected-brain.exe").unlink()
        self.assertFalse(self.install().success)

    def test_busy_writer_blocks_setup(self):
        self.backend.busy = True
        before = snapshot(self.roots.app_root)
        self.assertFalse(self.install().success)
        self.assertEqual(snapshot(self.roots.app_root), before)
        self.assertFalse(self.vault.exists())

    def test_settings_are_saved_and_a_repeat_keeps_them(self):
        self.assertTrue(self.install(summary_provider="codex", provider_fallback=False).success)
        preferences = ConfigStore(self.roots.data_root).read()["preferences"]
        self.assertEqual((preferences["summary_provider"], preferences["provider_fallback"]), ("codex", False))
        self.assertTrue(self.install().success)
        self.assertEqual(ConfigStore(self.roots.data_root).read()["preferences"]["summary_provider"], "codex")

    def test_unknown_or_invalid_settings_change_nothing(self):
        before = snapshot(self.root)
        self.assertFalse(self.install(not_a_setting=True).success)
        self.assertFalse(self.install(briefing_time="9").success)
        self.assertEqual(snapshot(self.root), before)

    def test_fresh_native_install_renders_global_hooks_for_final_registered_uuid(self):
        from respected_brain.integrations.backend import NativeBackend
        self.backend = NativeBackend(self.roots.data_root)
        self.assertTrue(self.install(**{"integrations.global": True}).success)
        identity = json.loads((self.vault / ".respected.json").read_text())["vault_id"]
        content = self.global_hooks()
        self.assertIn(identity, content)
        self.assertIn(str(self.roots.app_root / "respected-brain.exe").replace("\\", "\\\\"), content)
        self.assertIn("respected-brain.exe", content)
        self.assertNotIn("python", content)

    def test_reinstall_preserves_user_note_and_project_config_bytes(self):
        self.assertTrue(self.install().success)
        path = self.vault / "knowledge/human-note.md"
        path.write_bytes("İnsan notu.\n".encode())
        settings = self.vault / ".claude/settings.json"
        settings.parent.mkdir()
        settings.write_bytes(b'{"myProjectSetting":true}')
        before = snapshot(self.vault)
        self.assertTrue(self.install().success)
        self.assertEqual(snapshot(self.vault), before)

    def test_reinstall_applies_requested_vault_shortcut(self):
        self.assertTrue(self.install().success)
        result = self.install(**{"integrations.shortcut": True})
        self.assertTrue(result.success, result.conflicts)
        rows = [value for (kind, key), value in self.backend.records.items() if kind == "shortcut"]
        self.assertEqual(len(rows), 1)
        self.assertIn("open --vault-id", json.loads(rows[0])["arguments"])

    def test_requested_global_failure_is_reported_and_existing_notes_retained(self):
        self.assertTrue(self.install().success)
        before = snapshot(self.vault)
        with patch.object(self.backend, "apply", side_effect=OSError("global failure")):
            result = self.install(**{"integrations.global": True})
        self.assertFalse(result.success)
        self.assertEqual(snapshot(self.vault), before)

    def test_integration_failure_rolls_back_a_fresh_setup_but_leaves_the_program(self):
        program = snapshot(self.roots.app_root)
        with patch.object(self.backend, "apply", side_effect=OSError("integration failed")):
            result = self.install(**{"integrations.global": True})
        self.assertFalse(result.success)
        self.assertFalse(self.vault.exists())
        self.assertEqual(snapshot(self.roots.app_root), program)

    def test_mcp_registration_uses_installed_launcher_and_uuid(self):
        result = self.install(**{"integrations.mcp": True})
        self.assertTrue(result.success, result.conflicts)
        records = [json.loads(value) for (kind, key), value in self.backend.records.items() if kind == "mcp" and value and "mcpServers" in json.loads(value)]
        self.assertTrue(records)
        for record in records:
            command = record["mcpServers"]["respected-brain"]
            self.assertEqual(command["command"], str(self.roots.app_root / "respected-brain.exe"))
            self.assertEqual(command["args"][0], "mcp")
            self.assertIn("--vault-id", command["args"])

    def test_vault_gets_no_local_hook_folders_and_notes_survive_maintenance(self):
        from respected_brain.integrations.backend import NativeBackend
        from respected_brain.installation.repair import repair
        from respected_brain.installation.uninstall import uninstall
        from respected_brain.vault.registry import build_context
        names = ('.agents/hooks.json', '.claude/settings.json', '.codex/hooks.json', '.cursor/hooks.json', '.gemini/settings.json')
        for purge in (True, False):
            with self.subTest(purge=purge):
                root = self.root / str(purge)
                (root / 'home').mkdir(parents=True)
                roots = Roots(root / 'app', root / 'data', root / 'vault')
                seed_package(roots.app_root)
                backend = NativeBackend(roots.data_root)
                result = setup(roots, roots.default_vault, values=OFF, backend=backend, platform='windows-native', home=root / 'home')
                self.assertTrue(result.success, result.conflicts)
                ctx = build_context(roots, ConfigStore(roots.data_root), vault=roots.default_vault, vault_id=None, env={})
                notes = note_hashes(roots.default_vault)
                self.assertTrue(all(not (roots.default_vault / name).exists() for name in names))
                result = repair(ctx, backend=backend)
                self.assertTrue(result.success, result.conflicts)
                self.assertTrue(all(not (roots.default_vault / name).exists() for name in names))
                result = uninstall(ctx, backend=backend, purge_data=purge)
                self.assertTrue(result.success, result.conflicts)
                self.assertEqual(note_hashes(roots.default_vault), notes)
                self.assertTrue((roots.app_root / 'respected-brain.exe').is_file(), "the program is the installer's to remove")
                self.assertFalse((roots.data_root / 'install-manifest.json').exists())

    def test_an_install_from_before_the_rename_moves_to_respected_brain_and_uninstalls_clean(self):
        """Beta.2 registered the MCP server as 'respected-vault' (and its Antigravity tool folder). A repair moves both; uninstall restores the user's files."""
        from respected_brain.integrations import rendering
        from respected_brain.integrations.backend import NativeBackend
        from respected_brain.installation.repair import repair
        from respected_brain.installation.uninstall import uninstall
        from respected_brain.vault.registry import build_context
        home = self.root / "home"
        (home / ".gemini").mkdir()
        original = json.dumps({"mcpServers": {"other": {"command": "npx", "args": ["x"]}}, "theme": "dark"}, indent=2) + "\n"
        (home / ".claude.json").write_text(original, encoding="utf-8")
        backend = NativeBackend(self.roots.data_root)
        with patch.object(rendering, "MCP_SERVER", "respected-vault"):   # what the older Brain wrote
            result = setup(self.roots, self.vault, values={"user_name": "Ada", "assistant_name": "Atlas", **OFF, "integrations.mcp": True},
                           backend=backend, platform="windows-native", home=home)
        self.assertTrue(result.success, result.conflicts)
        self.assertIn("respected-vault", json.loads((home / ".claude.json").read_text(encoding="utf-8"))["mcpServers"])
        self.assertTrue((home / ".gemini/antigravity-ide/mcp/respected-vault/instructions.md").is_file())
        ctx = build_context(self.roots, ConfigStore(self.roots.data_root), vault=self.vault, vault_id=None, env={})
        result = repair(ctx, backend=backend)
        self.assertTrue(result.success, result.conflicts)
        servers = json.loads((home / ".claude.json").read_text(encoding="utf-8"))["mcpServers"]
        self.assertEqual(sorted(servers), ["other", "respected-brain"])
        self.assertTrue((home / ".gemini/antigravity-ide/mcp/respected-brain/instructions.md").is_file())
        self.assertFalse((home / ".gemini/antigravity-ide/mcp/respected-vault").exists())
        result = uninstall(ctx, backend=backend, purge_data=True)
        self.assertTrue(result.success, result.conflicts)
        self.assertEqual(json.loads((home / ".claude.json").read_text(encoding="utf-8")), json.loads(original))
        self.assertEqual(sorted(path.name for path in (home / ".gemini").rglob("*")), [], "the folders our registrations created are gone")

    def test_install_rolls_back_when_install_health_fails(self):
        from respected_brain.integrations.backend import NativeBackend
        self.backend = NativeBackend(self.roots.data_root)
        with patch('respected_brain.installation.payload.validate_installed_health', side_effect=OSError('health failure')):
            result = self.install()
        self.assertFalse(result.success)
        self.assertEqual(result.conflicts, ('health failure',))
        self.assertFalse(self.vault.exists())


if __name__ == "__main__":
    unittest.main()
