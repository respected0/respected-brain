"""POSIX installation contracts with isolated fake payloads; no native build claim."""
import hashlib
import json
import os
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch
from respected_brain.core.config import ConfigStore
from respected_brain.core.paths import Roots
from respected_brain.vault.registry import build_context
from respected_brain.installation.setup import setup as production_setup
from respected_brain.installation.repair import repair
from respected_brain.installation.uninstall import uninstall
from respected_brain.installation.ownership import read_manifest, prove_ownership
from tests.support.packages import seed_package
from tests.support.files import note_hashes
from tests.support.fakes import Backend


class FoundationPosixInstallTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.home = self.root / "Ada's home 🧠"
        self.home.mkdir()
        self.vault = self.root / "vault"
        self.roots = Roots(self.root / "app", self.root / "data", self.vault)
        self.backend = Backend()
        self.flags = dict.fromkeys(("global", "mcp", "schedule", "shortcut"), False)
        self.profile = {"platform":"posix", "user_home":str(self.home)}
        self.package = seed_package(self.roots.app_root)  # setup.sh copied the program here
        executable = self.package / "respected-brain.exe"
        executable.rename(self.package / "respected-brain")
        manifest = json.loads((self.package / "distribution.json").read_text())
        manifest["platform"] = "linux"
        manifest["launcher"] = "respected-brain"
        manifest["files"]["respected-brain"] = manifest["files"].pop("respected-brain.exe")
        (self.package / "distribution.json").write_text(json.dumps(manifest))
        (self.package / "respected-brain").chmod(0o755)
        for fake in (patch("sys.platform", "linux"), patch("respected_brain.installation.payload.validate_installed_health", return_value=None)):
            fake.start()
            self.addCleanup(fake.stop)
        self.launcher = self.home / ".local/bin/respected-brain"
    def setup(self):
        return production_setup(self.roots, self.vault, values={"integrations." + key: value for key, value in self.flags.items()},
                                backend=self.backend, platform=self.profile.get("platform"), home=self.home)

    def install(self):
        result = self.setup()
        self.assertTrue(result.success, result.conflicts)
        return build_context(self.roots, ConfigStore(self.roots.data_root), vault=self.vault, vault_id=None, env={})
    def test_unreadable_distribution_manifest_fails_and_is_left_alone(self):
        target = self.roots.app_root / "distribution.json"
        target.write_bytes(b"user-owned-sentinel")
        self.assertFalse(self.setup().success)
        self.assertEqual(target.read_bytes(), b"user-owned-sentinel")

    def test_default_linux_profile_persists_resolved_platform(self):
        self.profile.pop("platform")
        ctx = self.install()
        from respected_brain.installation.operations import validate_manifest_roots
        self.assertEqual(ctx.config["vaults"][ctx.paths.vault_id]["settings"].get("platform"), "posix")
        validate_manifest_roots(ctx, read_manifest(ctx.paths.data_root / "install-manifest.json"))

    def test_posix_schedule_files_are_kept_when_global_is_disabled(self):
        ctx = self.install()
        ConfigStore(ctx.paths.data_root).update(lambda value: value["integrations"].update(schedule=True))
        from respected_brain.installation.ownership import OwnershipManifest
        from respected_brain.installation.operations import plan_connections
        from respected_brain.integrations.backend import ExternalChange
        name = "respected-morning-briefing-" + ctx.paths.vault_id
        rows = tuple(ExternalChange("file", str(self.home / ".config/systemd/user" / (name + suffix)), None, b"owned schedule") for suffix in (".service", ".timer"))
        for row in rows:
            self.backend.records[(row.kind, row.key)] = row.after
        with patch("respected_brain.integrations.rendering.plan_integrations", return_value=()):
            changes, owned = plan_connections(ctx, self.backend, OwnershipManifest(3, (), rows))
        self.assertEqual(changes, ())
        self.assertEqual(owned, rows)

    def test_required_launcher_is_owned_independent_of_all_disabled_integrations(self):
        ctx = self.install()
        self.assertTrue(self.launcher.is_file(), "Linux install must create the required PATH launcher")
        text = self.launcher.read_text()
        self.assertTrue(text.startswith("#!/bin/sh\n"))
        self.assertIn("respected-brain", text)
        self.assertIn('"$@"', text)
        manifest = read_manifest(self.roots.data_root / "install-manifest.json")
        self.assertTrue(any(item.role == "launcher" and item.path == self.launcher for item in manifest.files))
        self.assertTrue(prove_ownership(self.launcher, manifest))
        self.assertEqual(ConfigStore(ctx.paths.data_root).read()["integrations"], self.flags)
    def test_unknown_launcher_collision_is_retained_and_install_rolls_back(self):
        self.launcher.parent.mkdir(parents=True)
        self.launcher.write_bytes(b"user launcher")
        self.assertFalse(self.setup().success)
        self.assertEqual(self.launcher.read_bytes(), b"user launcher")
        self.assertTrue((self.roots.app_root / "respected-brain").exists(), "the program is setup.sh's, not the product's")
    def test_repair_and_uninstall_keep_notes_and_manage_launcher(self):
        ctx = self.install()
        before = note_hashes(self.vault)
        self.assertTrue(repair(ctx, backend=self.backend).success)
        self.assertTrue(self.launcher.is_file())
        self.launcher.unlink()
        result = repair(ctx, backend=self.backend)
        self.assertTrue(result.success, result.conflicts)
        self.assertTrue(self.launcher.is_file())
        self.assertTrue(uninstall(ctx, backend=self.backend).success)
        self.assertFalse(self.launcher.exists())
        self.assertEqual(note_hashes(self.vault), before)
    def test_application_permission_changes_break_ownership_proof(self):
        self.install()
        binary = self.roots.app_root / "respected-brain"
        original = stat.S_IMODE(binary.stat().st_mode)
        binary.chmod(0o444)
        try:
            self.assertFalse(prove_ownership(binary, read_manifest(self.roots.data_root / "install-manifest.json")))
        finally:
            binary.chmod(original)

    def test_owned_launcher_user_content_edit_is_retained(self):
        ctx = self.install()
        self.assertTrue(self.launcher.is_file(), "Required launcher missing")
        self.launcher.write_bytes(b"user edit")
        result = repair(ctx, backend=self.backend)
        self.assertFalse(result.success)
        self.assertEqual(self.launcher.read_bytes(), b"user edit")
        result = uninstall(ctx, backend=self.backend)
        self.assertFalse(result.success)
        self.assertEqual(self.launcher.read_bytes(), b"user edit")
    def test_owned_launcher_permission_edit_is_retained(self):
        ctx = self.install()
        self.assertTrue(self.launcher.is_file(), "Required launcher missing")
        self.launcher.chmod(0o444)
        try:
            manifest = read_manifest(self.roots.data_root / "install-manifest.json")
            self.assertFalse(prove_ownership(self.launcher, manifest))
            result = repair(ctx, backend=self.backend)
            self.assertFalse(result.success)
            self.assertEqual(stat.S_IMODE(self.launcher.stat().st_mode) & 0o222, 0)
        finally:
            self.launcher.chmod(0o666)
    def test_fresh_health_failure_removes_only_product_launcher(self):
        sentinel = self.home / "sentinel"
        sentinel.write_bytes(b"user")
        with patch("respected_brain.installation.payload.validate_installed_health", side_effect=OSError("fault")):
            result = self.setup()
        self.assertFalse(result.success)
        self.assertFalse(self.launcher.exists())
        self.assertEqual(sentinel.read_bytes(), b"user")
    @unittest.skipIf(os.name == "nt", "POSIX shell/executable permissions require an actual POSIX host")
    def test_required_launcher_is_executable_and_quotes_application_path(self):
        ctx = self.install()
        self.assertTrue(os.access(self.launcher, os.X_OK))
        import shlex
        command = self.launcher.read_text().splitlines()[1]
        self.assertEqual(shlex.split(command)[:2], ["exec", str(self.roots.app_root / "respected-brain")])

class PosixPackagingEntrypointsTest(unittest.TestCase):
    def test_native_setup_scripts_copy_the_program_and_forward_to_the_product(self):
        root = Path(__file__).resolve().parents[2]
        for name in ("packaging/linux/setup.sh", "packaging/macos/setup.command"):
            path = root / name
            self.assertTrue(path.is_file(), name)
            self.assertNotIn(b"\r", path.read_bytes(), "POSIX shebang files require LF line endings")
            text = path.read_text()
            for token in ("cp -R", " setup --platform posix", " repair", " uninstall", "--uninstall", '"$@"'):
                self.assertIn(token, text)
            self.assertNotIn("--package", text)
            self.assertNotIn("python", text.lower())
