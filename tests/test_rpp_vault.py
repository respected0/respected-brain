"""Hub-driven vault creation through RPP lifecycle.apply install (temporary roots only)."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from respectedbrain.rpp import server as rpp


class CreateVaultTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="rpp-vault-")
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name).resolve()
        self.data = self.base / "data"
        self.data.mkdir()

    def install(self, vault, operation_id="op-vault-0001", **extra):
        request = {"rpp": "1.1", "op": "lifecycle.apply", "operation_id": operation_id,
                   "payload": {"action": "install", "target": {"vault_path": str(vault), **extra}}}
        return rpp.serve(json.dumps(request), data_root=self.data)

    def manifest(self):
        return rpp.serve(json.dumps({"rpp": "1.1", "op": "manifest", "payload": {}}), data_root=self.data)["result"]

    def test_creates_registers_and_reports_installed(self):
        vault = self.base / "My Vault"
        response = self.install(vault, profile={"USER_NAME": "Test User"})
        self.assertTrue(response["ok"], response)
        self.assertEqual(response["result"]["status"], "applied")
        self.assertTrue(any(vault.iterdir()))
        manifest = self.manifest()
        self.assertTrue(manifest["installed"])
        self.assertEqual(manifest["roots"]["vault"], str(vault))
        replay = self.install(vault, profile={"USER_NAME": "Test User"})
        self.assertTrue(replay["ok"], replay)
        health = rpp.serve(json.dumps({"rpp": "1.1", "op": "health", "payload": {}}), data_root=self.data)["result"]
        self.assertTrue(next(c for c in health["checks"] if c["name"] == "vault_registered")["ok"])

    def test_refuses_nonempty_folders_second_vaults_and_bad_paths(self):
        full = self.base / "notes"
        full.mkdir()
        (full / "keep.md").write_text("mine", encoding="utf-8")
        denied = self.install(full)
        self.assertFalse(denied["ok"])
        self.assertEqual(denied["error"]["code"], "PERMISSION_DENIED")
        self.assertEqual((full / "keep.md").read_text(encoding="utf-8"), "mine")
        relative = self.install(Path("relative/vault"), operation_id="op-vault-0002")
        self.assertEqual(relative["error"]["code"], "BAD_REQUEST")
        inside = self.install(self.data / "vault", operation_id="op-vault-0003")
        self.assertEqual(inside["error"]["code"], "BAD_REQUEST")
        self.assertTrue(self.install(self.base / "first", operation_id="op-vault-0004")["ok"])
        second = self.install(self.base / "second", operation_id="op-vault-0005")
        self.assertEqual(second["error"]["code"], "LIFECYCLE_CONFLICT")
        self.assertFalse((self.base / "second").exists())


if __name__ == "__main__":
    unittest.main()


class InstallStateTest(unittest.TestCase):
    def test_changed_or_missing_owned_files_report_repair_needed_but_config_changes_do_not(self):
        import hashlib
        with tempfile.TemporaryDirectory(prefix="rpp-state-") as name:
            base = Path(name).resolve()
            data = base / "data"
            data.mkdir()
            app_file, config = base / "app.bin", base / "config.json"
            app_file.write_bytes(b"one")
            config.write_bytes(b"cfg")
            rows = [{"path": str(app_file), "sha256": hashlib.sha256(b"one").hexdigest(), "role": "application"},
                    {"path": str(config), "sha256": hashlib.sha256(b"cfg").hexdigest(), "role": "technical"}]
            (data / "install-manifest.json").write_text(json.dumps({"schema_version": 3, "files": rows, "external": []}), encoding="utf-8")
            state = lambda: rpp.serve(json.dumps({"rpp": "1.1", "op": "manifest", "payload": {}}), data_root=data)["result"]["install_state"]
            self.assertEqual(state(), "installed")
            config.write_bytes(b"changed settings")
            self.assertEqual(state(), "installed")
            app_file.write_bytes(b"tampered")
            self.assertEqual(state(), "repair-needed")
            app_file.unlink()
            self.assertEqual(state(), "repair-needed")
