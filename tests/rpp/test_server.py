"""Tests for the RPP v1.1 entry point: v1.0 compatibility plus v1.1 additions.

Temporary data roots only; no live AppData or vault is touched.
"""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from respectedbrain.rpp import server as rpp


class RppTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="rpp-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve() / "data"
        self.root.mkdir()

    def call(self, request, version="1.0"):
        response = rpp.serve(json.dumps(request), data_root=self.root)
        self.assertEqual(set(response), {"rpp", "ok", "operation_id", "result", "error"})
        self.assertEqual(response["rpp"], version)
        return response

    # --- v1.0 behaviour (unchanged) -------------------------------------------------

    def test_manifest_lists_real_capabilities(self):
        response = self.call({"rpp": "1.0", "op": "manifest"})
        self.assertTrue(response["ok"])
        result = response["result"]
        self.assertEqual(result["product_id"], "respected-secondbrain")
        self.assertEqual(result["protocol"], {"min": "1.0", "max": "1.1"})
        self.assertTrue(result["settings_supported"])
        self.assertIn("recall", result["capabilities"])
        self.assertTrue(set(result["capabilities"]) <= set(rpp.CAPABILITIES))
        self.assertTrue(result["product_version"])

    def test_bad_json_is_bad_request(self):
        response = rpp.serve("{not json", data_root=self.root)
        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "BAD_REQUEST")

    def test_unknown_op(self):
        response = self.call({"rpp": "1.0", "op": "does.not.exist"})
        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "UNKNOWN_OP")

    def test_unsupported_protocol(self):
        response = self.call({"rpp": "2.0", "op": "manifest"})
        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "PROTOCOL_UNSUPPORTED")

    def test_health_reports_real_checks(self):
        response = self.call({"rpp": "1.0", "op": "health"})
        self.assertTrue(response["ok"])
        names = [check["name"] for check in response["result"]["checks"]]
        self.assertIn("data_root_writable", names)
        self.assertIn("config_loads", names)
        self.assertIn(response["result"]["status"], ("healthy", "degraded", "unhealthy"))

    def test_schema_exposes_allowlisted_keys(self):
        response = self.call({"rpp": "1.0", "op": "settings.schema"})
        keys = {field["key"] for field in response["result"]["fields"]}
        self.assertEqual(keys, set(rpp._SCHEMA))
        self.assertIn("summary_provider", keys)
        self.assertIn("integrations.mcp", keys)

    def test_validate_rejects_unknown_key(self):
        response = self.call({"rpp": "1.0", "op": "settings.validate",
                              "payload": {"settings": {"not_a_key": 1}}})
        self.assertTrue(response["ok"])
        self.assertFalse(response["result"]["valid"])
        self.assertEqual(response["result"]["errors"][0]["key"], "not_a_key")

    def test_validate_rejects_bad_enum(self):
        response = self.call({"rpp": "1.0", "op": "settings.validate",
                              "payload": {"settings": {"summary_provider": "nope"}}})
        self.assertFalse(response["result"]["valid"])

    def test_apply_requires_operation_id(self):
        response = self.call({"rpp": "1.0", "op": "settings.apply",
                              "payload": {"settings": {"provider_fallback": False}}})
        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "BAD_REQUEST")

    def test_apply_invalid_writes_nothing(self):
        response = self.call({"rpp": "1.0", "op": "settings.apply", "operation_id": "op-invalid",
                              "payload": {"settings": {"summary_provider": "nope"}}})
        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "INVALID_SETTINGS")
        self.assertFalse((self.root / "config.json").exists())
        self.assertFalse((self.root / "receipts").exists())

    def test_apply_valid_then_readback(self):
        response = self.call({"rpp": "1.0", "op": "settings.apply", "operation_id": "op-apply-1",
                              "payload": {"settings": {"summary_provider": "claude",
                                                       "integrations.mcp": True}}})
        self.assertTrue(response["ok"])
        receipt = response["result"]
        self.assertEqual(receipt["status"], "applied")
        self.assertTrue((self.root / "receipts" / "op-apply-1.json").exists())

        stored = json.loads((self.root / "config.json").read_text(encoding="utf-8"))
        self.assertEqual(stored["preferences"]["summary_provider"], "claude")
        self.assertTrue(stored["integrations"]["mcp"])

        readback = self.call({"rpp": "1.0", "op": "settings.readback"})
        self.assertEqual(readback["result"]["source"], "file")
        self.assertEqual(readback["result"]["settings"]["summary_provider"], "claude")
        self.assertTrue(readback["result"]["settings"]["integrations.mcp"])
        self.assertIs(readback["result"]["settings"]["provider_fallback"], True)

    def test_assistant_name_is_a_product_setting_with_a_length_limit(self):
        applied = self.call({"rpp": "1.0", "op": "settings.apply", "operation_id": "op-name-1",
                             "payload": {"settings": {"assistant_name": "Jarvis"}}})
        self.assertTrue(applied["ok"])
        readback = self.call({"rpp": "1.0", "op": "settings.readback"})
        self.assertEqual(readback["result"]["settings"]["assistant_name"], "Jarvis")
        tooLong = self.call({"rpp": "1.0", "op": "settings.validate", "payload": {"settings": {"assistant_name": "x" * 41}}})
        self.assertFalse(tooLong["result"]["valid"])

    def test_readback_defaults_without_config(self):
        response = self.call({"rpp": "1.0", "op": "settings.readback"})
        self.assertTrue(response["ok"])
        self.assertEqual(response["result"]["source"], "defaults")
        self.assertEqual(response["result"]["settings"]["summary_provider"], "auto")

    def test_apply_idempotent_replay(self):
        request = {"rpp": "1.0", "op": "settings.apply", "operation_id": "op-replay",
                   "payload": {"settings": {"provider_fallback": False}}}
        first = self.call(request)
        before = (self.root / "config.json").read_bytes()
        second = self.call(request)
        self.assertTrue(second["ok"])
        self.assertEqual(second["result"]["settings_sha256"],
                         first["result"]["settings_sha256"])
        self.assertEqual((self.root / "config.json").read_bytes(), before)

    def test_apply_operation_id_conflict(self):
        self.call({"rpp": "1.0", "op": "settings.apply", "operation_id": "op-conflict",
                   "payload": {"settings": {"provider_fallback": False}}})
        conflict = self.call({"rpp": "1.0", "op": "settings.apply", "operation_id": "op-conflict",
                              "payload": {"settings": {"provider_fallback": True}}})
        self.assertFalse(conflict["ok"])
        self.assertEqual(conflict["error"]["code"], "OPERATION_ID_CONFLICT")

    def test_receipt_has_no_settings_values(self):
        self.call({"rpp": "1.0", "op": "settings.apply", "operation_id": "op-receipt",
                   "payload": {"settings": {"integrations.schedule": True}}})
        receipt = json.loads((self.root / "receipts" / "op-receipt.json").read_text(encoding="utf-8"))
        self.assertEqual(set(receipt), {"operation_id", "op", "status", "applied_at", "settings_sha256"})

    def test_readback_returns_only_schema_keys(self):
        response = self.call({"rpp": "1.0", "op": "settings.readback"})
        self.assertEqual(set(response["result"]["settings"]), set(rpp._SCHEMA))

    # --- v1.1 additions -------------------------------------------------------------

    def test_v11_negotiation_echoes_requested_version(self):
        response = self.call({"rpp": "1.1", "op": "manifest"}, version="1.1")
        self.assertTrue(response["ok"])
        self.assertEqual(response["result"]["protocol"], {"min": "1.0", "max": "1.1"})
        still = self.call({"rpp": "1.0", "op": "manifest"})
        self.assertEqual(still["rpp"], "1.0")

    def test_v11_manifest_richer_keys(self):
        result = self.call({"rpp": "1.1", "op": "manifest"}, version="1.1")["result"]
        self.assertIsInstance(result["installed"], bool)
        self.assertIn(result["install_state"], ("absent", "installed", "update-available", "repair-needed"))
        self.assertIn("product_version", result)
        roots = result["roots"]
        self.assertEqual(set(roots), {"data", "app", "vault"})
        self.assertTrue(all(value is None or isinstance(value, str) for value in roots.values()))
        self.assertEqual(roots["data"], str(self.root))
        details = result["capability_details"]
        self.assertTrue(details)
        for item in details:
            self.assertTrue({"id", "since", "ops"} <= set(item))
            self.assertIn(item["since"], ("1.0", "1.1"))
            self.assertIsInstance(item["ops"], list)
        self.assertTrue(set(result["capabilities"]) <= {item["id"] for item in details})

    def test_v11_manifest_reports_installed(self):
        self.assertFalse(self.call({"rpp": "1.1", "op": "manifest"}, version="1.1")["result"]["installed"])
        (self.root / "install-manifest.json").write_text("{}", encoding="utf-8")
        result = self.call({"rpp": "1.1", "op": "manifest"}, version="1.1")["result"]
        self.assertTrue(result["installed"])
        self.assertEqual(result["install_state"], "installed")

    def test_v11_ops_require_protocol_1_1(self):
        for op in ("lifecycle.plan", "lifecycle.apply", "lifecycle.status",
                   "lifecycle.rollback", "operation.receipt"):
            response = self.call({"rpp": "1.0", "op": op})
            self.assertFalse(response["ok"])
            self.assertEqual(response["error"]["code"], "UNSUPPORTED_OP")
            self.assertIn("1.1", response["error"]["hint"])

    def test_operation_receipt_reads_settings_receipt(self):
        self.call({"rpp": "1.0", "op": "settings.apply", "operation_id": "op-shared-1",
                   "payload": {"settings": {"provider_fallback": False}}})
        stored = json.loads((self.root / "receipts" / "op-shared-1.json").read_text(encoding="utf-8"))
        response = self.call({"rpp": "1.1", "op": "operation.receipt",
                              "payload": {"operation_id": "op-shared-1"}}, version="1.1")
        self.assertTrue(response["ok"])
        self.assertEqual(response["result"], stored)


if __name__ == "__main__":
    unittest.main()
