"""Lifecycle op tests for RPP v1.1: dry-run plans, receipts, rollback, delegation.

Every root is a temporary directory; nothing touches the live AppData or vault.
"""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch

from respectedbrain.rpp import server as rpp, lifecycle as rpp_lifecycle


ACTIONS = ("install", "update", "repair", "uninstall")


class LifecycleTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="rpp-life-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve() / "data"
        self.root.mkdir()

    def call(self, request, version="1.1"):
        response = rpp.serve(json.dumps(request), data_root=self.root)
        self.assertEqual(set(response), {"rpp", "ok", "operation_id", "result", "error"})
        self.assertEqual(response["rpp"], version)
        return response

    def apply(self, action, operation_id="op-life-0001", target=None):
        return self.call({"rpp": "1.1", "op": "lifecycle.apply", "operation_id": operation_id,
                          "payload": {"action": action, "target": target or {}}})

    def receipt_path(self, operation_id):
        return self.root / "receipts" / f"{operation_id}.json"

    # --- dry run --------------------------------------------------------------------

    def test_plan_is_read_only_for_every_action(self):
        for action in ACTIONS:
            response = self.call({"rpp": "1.1", "op": "lifecycle.plan",
                                  "payload": {"action": action, "target": {}}})
            self.assertTrue(response["ok"], response.get("error"))
            result = response["result"]
            self.assertEqual(result["action"], action)
            self.assertIs(result["dry_run"], True)
            steps = result["plan"]["steps"]
            self.assertTrue(steps)
            for step in steps:
                self.assertTrue({"id", "action", "summary", "reversible", "irreversible_reason"} <= set(step))
                self.assertIsInstance(step["reversible"], bool)
                self.assertEqual(step["irreversible_reason"] is None, step["reversible"])
        self.assertFalse((self.root / "receipts").exists())
        self.assertFalse((self.root / "config.json").exists())

    def test_plan_marks_irreversible_actions(self):
        def steps(action):
            return self.call({"rpp": "1.1", "op": "lifecycle.plan",
                              "payload": {"action": action}})["result"]["plan"]["steps"]
        self.assertTrue(all(step["reversible"] for step in steps("update")))
        self.assertTrue(all(step["reversible"] for step in steps("repair")))
        self.assertTrue(any(not step["reversible"] for step in steps("install")))
        self.assertTrue(any(not step["reversible"] for step in steps("uninstall")))

    def test_plan_rejects_unknown_action(self):
        response = self.call({"rpp": "1.1", "op": "lifecycle.plan", "payload": {"action": "explode"}})
        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "BAD_REQUEST")

    # --- apply / status / receipt ---------------------------------------------------

    def test_apply_repair_writes_applied_receipt(self):
        response = self.apply("repair", "op-repair-001")
        self.assertTrue(response["ok"], response.get("error"))
        self.assertEqual(response["operation_id"], "op-repair-001")
        self.assertEqual(response["result"]["status"], "applied")
        self.assertEqual(response["result"]["action"], "repair")
        stored = json.loads(self.receipt_path("op-repair-001").read_text(encoding="utf-8"))
        self.assertEqual(stored["operation_id"], "op-repair-001")
        self.assertEqual(stored["action"], "repair")
        self.assertEqual(stored["status"], "applied")
        self.assertNotIn("usage", stored)

    def test_apply_requires_operation_id(self):
        response = self.call({"rpp": "1.1", "op": "lifecycle.apply",
                              "payload": {"action": "repair"}})
        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "BAD_REQUEST")

    def test_apply_replay_is_idempotent(self):
        first = self.apply("repair", "op-repair-002")
        second = self.apply("repair", "op-repair-002")
        self.assertTrue(second["ok"])
        self.assertEqual(second["result"], first["result"])

    def test_apply_same_id_different_action_conflicts(self):
        self.apply("repair", "op-repair-003")
        conflict = self.apply("update", "op-repair-003")
        self.assertFalse(conflict["ok"])
        self.assertEqual(conflict["error"]["code"], "LIFECYCLE_CONFLICT")

    def test_apply_same_id_different_target_conflicts(self):
        self.apply("repair", "op-target-1", target={"vault": "a"})
        conflict = self.apply("repair", "op-target-1", target={"vault": "b"})
        self.assertFalse(conflict["ok"])
        self.assertEqual(conflict["error"]["code"], "LIFECYCLE_CONFLICT")

    def test_status_matches_receipt_and_unknown_is_not_found(self):
        self.apply("repair", "op-repair-004")
        status = self.call({"rpp": "1.1", "op": "lifecycle.status",
                            "payload": {"operation_id": "op-repair-004"}})
        receipt = self.call({"rpp": "1.1", "op": "operation.receipt",
                             "payload": {"operation_id": "op-repair-004"}})
        self.assertTrue(status["ok"] and receipt["ok"])
        self.assertEqual(status["result"], receipt["result"])
        missing = self.call({"rpp": "1.1", "op": "operation.receipt",
                             "payload": {"operation_id": "op-missing-9"}})
        self.assertFalse(missing["ok"])
        self.assertEqual(missing["error"]["code"], "RECEIPT_NOT_FOUND")

    # --- rollback -------------------------------------------------------------------

    def test_rollback_reverses_and_is_idempotent(self):
        self.apply("repair", "op-repair-005")
        rollback = self.call({"rpp": "1.1", "op": "lifecycle.rollback",
                              "payload": {"operation_id": "op-repair-005"}})
        self.assertTrue(rollback["ok"], rollback.get("error"))
        self.assertEqual(rollback["result"]["status"], "rolled_back")
        again = self.call({"rpp": "1.1", "op": "lifecycle.rollback",
                           "payload": {"operation_id": "op-repair-005"}})
        self.assertTrue(again["ok"])
        self.assertEqual(again["result"], rollback["result"])
        stored = json.loads(self.receipt_path("op-repair-005").read_text(encoding="utf-8"))
        self.assertEqual(stored["status"], "rolled_back")

    def test_rollback_refuses_irreversible_plan(self):
        steps = [{"id": "materialise", "action": "install", "summary": "s",
                  "reversible": False, "irreversible_reason": "creates notes"}]
        (self.root / "receipts").mkdir()
        self.receipt_path("op-irrev-001").write_text(json.dumps(
            {"operation_id": "op-irrev-001", "op": "lifecycle.apply", "action": "install",
             "status": "applied", "applied_at": "t", "steps": steps}), encoding="utf-8")
        response = self.call({"rpp": "1.1", "op": "lifecycle.rollback",
                              "payload": {"operation_id": "op-irrev-001"}})
        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "ROLLBACK_UNAVAILABLE")

    def test_rollback_rejects_non_lifecycle_receipt(self):
        self.call({"rpp": "1.1", "op": "settings.apply", "operation_id": "op-settings-1",
                   "payload": {"settings": {"provider_fallback": False}}})
        response = self.call({"rpp": "1.1", "op": "lifecycle.rollback",
                              "payload": {"operation_id": "op-settings-1"}})
        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "ROLLBACK_UNAVAILABLE")

    def test_rollback_missing_receipt(self):
        response = self.call({"rpp": "1.1", "op": "lifecycle.rollback",
                              "payload": {"operation_id": "op-missing-9"}})
        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "RECEIPT_NOT_FOUND")

    # --- delegation to the installation engine --------------------------------------

    def test_apply_delegates_to_installation_engine(self):
        context, backend = object(), object()
        outcome = types.SimpleNamespace(success=True, conflicts=())
        with patch.object(rpp_lifecycle, "_installed", return_value=True), \
                patch.object(rpp_lifecycle, "_context", return_value=context), \
                patch.object(rpp_lifecycle, "_backend", return_value=backend), \
                patch.object(rpp_lifecycle, "_delegate", return_value=outcome) as delegate:
            response = self.apply("repair", "op-deleg-0001")
        self.assertTrue(response["ok"], response.get("error"))
        delegate.assert_called_once_with("repair", context, backend)

    def test_apply_maps_engine_failure_to_partial(self):
        outcome = types.SimpleNamespace(success=False, conflicts=("engine refused",))
        with patch.object(rpp_lifecycle, "_installed", return_value=True), \
                patch.object(rpp_lifecycle, "_context", return_value=object()), \
                patch.object(rpp_lifecycle, "_backend", return_value=object()), \
                patch.object(rpp_lifecycle, "_delegate", return_value=outcome):
            response = self.apply("repair", "op-deleg-0002")
        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "LIFECYCLE_PARTIAL")
        stored = json.loads(self.receipt_path("op-deleg-0002").read_text(encoding="utf-8"))
        self.assertEqual(stored["status"], "failed")

    def test_apply_maps_engine_permission_error(self):
        error = rpp_lifecycle.LifecycleError("PERMISSION_DENIED", "needs elevation", "retry")
        with patch.object(rpp_lifecycle, "_installed", return_value=True), \
                patch.object(rpp_lifecycle, "_context", return_value=object()), \
                patch.object(rpp_lifecycle, "_backend", return_value=object()), \
                patch.object(rpp_lifecycle, "_delegate", side_effect=error):
            response = self.apply("update", "op-deleg-0003")
        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "PERMISSION_DENIED")
        self.assertFalse(self.receipt_path("op-deleg-0003").exists())


if __name__ == "__main__":
    unittest.main()
