"""Tests for the RPP 1 server: envelope, manifest, health and the settings operations.

Temporary data roots only; no live AppData or vault is touched.
"""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from respected_brain import settings as product_settings
from respected_brain.rpp import server as rpp


class RppTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="rpp-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve() / "data"
        self.root.mkdir()

    def call(self, request):
        response = rpp.serve(json.dumps({"rpp": "1", **request}), data_root=self.root)
        self.assertEqual(set(response), {"rpp", "ok", "operation_id", "result", "error"})
        self.assertEqual(response["rpp"], "1")
        return response

    def with_vault(self):
        (self.root / "config.json").write_text(json.dumps({"schema_version": 3, "active_vault_id": "v1", "preferences": {}, "integrations": {},
                                                           "vaults": {"v1": {"path": str(self.root.parent / "vault"), "settings": {"COMPANION": "Companion"}}}}), encoding="utf-8")

    def test_manifest_lists_the_real_operations_and_install_state(self):
        result = self.call({"op": "manifest"})["result"]
        self.assertEqual(result["product_id"], "respected-brain")
        self.assertEqual(result["rpp"], "1")
        self.assertEqual(result["capabilities"], sorted(rpp._OPS))
        self.assertTrue(result["product_version"])
        self.assertEqual((result["installed"], result["install_state"]), (False, "absent"))
        self.assertEqual(set(result["roots"]), {"data", "app", "vault"})
        self.assertEqual(result["roots"]["data"], str(self.root))
        (self.root / "install-manifest.json").write_text("{}", encoding="utf-8")
        result = self.call({"op": "manifest"})["result"]
        self.assertEqual((result["installed"], result["install_state"]), (True, "installed"))

    def test_bad_json_is_bad_request(self):
        response = rpp.serve("{not json", data_root=self.root)
        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "BAD_REQUEST")

    def test_absurdly_nested_json_is_bad_request(self):
        response = rpp.serve("[" * 100000 + "]" * 100000, data_root=self.root)
        self.assertEqual(response["error"]["code"], "BAD_REQUEST")

    def test_unknown_op(self):
        response = self.call({"op": "does.not.exist"})
        self.assertEqual(response["error"]["code"], "UNKNOWN_OP")
        self.assertNotIn("lifecycle", response["error"]["hint"])

    def test_only_protocol_1_is_spoken(self):
        for version in ("1.0", "1.1", "2", None):
            response = rpp.serve(json.dumps({"rpp": version, "op": "manifest"}), data_root=self.root)
            self.assertFalse(response["ok"])
            self.assertEqual(response["error"]["code"], "UNSUPPORTED_VERSION")

    def test_installing_is_not_a_protocol_operation(self):
        for op in ("lifecycle.plan", "lifecycle.apply", "lifecycle.status", "lifecycle.rollback", "operation.receipt"):
            self.assertEqual(self.call({"op": op})["error"]["code"], "UNKNOWN_OP")

    def test_health_reports_real_checks(self):
        response = self.call({"op": "health"})
        names = [check["name"] for check in response["result"]["checks"]]
        self.assertEqual(names, ["data_root_writable", "config_loads", "vault_registered"])
        self.assertEqual(response["result"]["status"], "degraded")

    def test_health_notices_a_vault_folder_that_is_gone_and_is_healthy_when_it_is_back(self):
        self.with_vault()
        gone = self.call({"op": "health"})["result"]
        self.assertEqual([check["name"] for check in gone["checks"]][-1], "vault_folder")
        self.assertEqual(gone["status"], "degraded")
        (self.root.parent / "vault").mkdir()
        self.assertEqual(self.call({"op": "health"})["result"]["status"], "healthy")

    def test_schema_is_the_product_settings_schema_in_turkish(self):
        fields = self.call({"op": "settings.schema"})["result"]["fields"]
        self.assertEqual(fields, product_settings.schema())
        self.assertTrue(all(field["label"] and field["help"] for field in fields))
        self.assertIn("briefing_time", {field["key"] for field in fields})

    def test_validate_rejects_unknown_keys_bad_values_and_profile_without_vault(self):
        for settings in ({"not_a_key": 1}, {"summary_provider": "nope"}, {"briefing_time": "25:00"},
                         {"integrations.clients": "claude,notepad"}, {"assistant_name": "Jarvis"}):
            result = self.call({"op": "settings.validate", "payload": {"settings": settings}})["result"]
            self.assertFalse(result["valid"], settings)

    def test_apply_requires_operation_id(self):
        response = self.call({"op": "settings.apply", "payload": {"settings": {"provider_fallback": False}}})
        self.assertEqual(response["error"]["code"], "BAD_REQUEST")

    def test_apply_invalid_writes_nothing(self):
        response = self.call({"op": "settings.apply", "operation_id": "op-invalid", "payload": {"settings": {"summary_provider": "nope"}}})
        self.assertEqual(response["error"]["code"], "INVALID_SETTINGS")
        self.assertFalse((self.root / "config.json").exists())
        self.assertFalse((self.root / "receipts").exists())

    def test_apply_valid_then_readback(self):
        response = self.call({"op": "settings.apply", "operation_id": "op-apply-1",
                              "payload": {"settings": {"summary_provider": "claude", "integrations.mcp": True, "briefing_time": "07:30",
                                                       "integrations.clients": "codex,claude"}}})
        self.assertEqual(response["result"]["status"], "applied")
        stored = json.loads((self.root / "config.json").read_text(encoding="utf-8"))
        self.assertEqual(stored["preferences"]["summary_provider"], "claude")
        self.assertEqual(stored["integrations"]["clients"], ["claude", "codex"])
        settings = self.call({"op": "settings.readback"})["result"]["settings"]
        self.assertEqual(set(settings), set(product_settings.SCHEMA))
        self.assertEqual((settings["summary_provider"], settings["briefing_time"], settings["integrations.clients"]), ("claude", "07:30", "claude,codex"))
        self.assertIs(settings["integrations.mcp"], True)
        self.assertIs(settings["provider_fallback"], True)

    def test_names_are_the_active_vaults_profile(self):
        self.with_vault()
        self.assertEqual(self.call({"op": "settings.readback"})["result"]["settings"]["assistant_name"], "")
        self.assertTrue(self.call({"op": "settings.apply", "operation_id": "op-name-1",
                                   "payload": {"settings": {"assistant_name": "Jarvis", "user_name": "Ayşe", "user_bio": "Geliştirici"}}})["ok"])
        stored = json.loads((self.root / "config.json").read_text(encoding="utf-8"))["vaults"]["v1"]["settings"]
        self.assertEqual((stored["COMPANION"], stored["USER_NAME"], stored["USER_BIO"]), ("Jarvis", "Ayşe", "Geliştirici"))
        self.assertFalse(self.call({"op": "settings.validate", "payload": {"settings": {"assistant_name": "x" * 41}}})["result"]["valid"])

    def test_apply_idempotent_replay_and_conflict(self):
        request = {"op": "settings.apply", "operation_id": "op-replay", "payload": {"settings": {"provider_fallback": False}}}
        first = self.call(request)
        before = (self.root / "config.json").read_bytes()
        second = self.call(request)
        self.assertEqual(second["result"]["settings_sha256"], first["result"]["settings_sha256"])
        self.assertEqual((self.root / "config.json").read_bytes(), before)
        conflict = self.call({**request, "payload": {"settings": {"provider_fallback": True}}})
        self.assertEqual(conflict["error"]["code"], "OPERATION_ID_CONFLICT")

    def test_receipt_has_no_settings_values(self):
        self.call({"op": "settings.apply", "operation_id": "op-receipt", "payload": {"settings": {"integrations.schedule": True}}})
        receipt = json.loads((self.root / "receipts" / "op-receipt.json").read_text(encoding="utf-8"))
        self.assertEqual(set(receipt), {"status", "applied_at", "settings_sha256"})


if __name__ == "__main__":
    unittest.main()
