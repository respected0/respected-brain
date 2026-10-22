"""integrations.plan is a read-only Safe Integration Layer preview (temporary home and roots)."""

from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from respected_brain.rpp import server as rpp


class IntegrationPlanTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="rpp-sil-")
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name).resolve()
        self.home, self.data, self.vault = self.base / "home", self.base / "data", self.base / "vault"
        (self.home / ".gemini").mkdir(parents=True)
        self.foreign = json.dumps({"mcpServers": {"someone-elses": {"command": "x", "args": []}}, "theme": "dark"})
        (self.home / ".claude.json").write_text(self.foreign, encoding="utf-8")
        patcher = patch.dict(os.environ, {"USERPROFILE": str(self.home), "HOME": str(self.home),
                                          "RESPECTED_APP_DIR": str(self.base / "app"), "RESPECTED_DATA_DIR": str(self.data)})
        patcher.start()
        self.addCleanup(patcher.stop)

    def plan(self, desired, **target):
        request = {"rpp": "1", "op": "integrations.plan", "operation_id": None,
                   "payload": {"target": {"vault_path": str(self.vault), "desired": desired, **target}}}
        return rpp.serve(json.dumps(request), data_root=self.data)

    def test_plan_lists_exact_changes_and_writes_nothing(self):
        response = self.plan({"mcp": True})
        self.assertTrue(response["ok"], response)
        result = response["result"]
        self.assertTrue(result["writes_nothing"])
        claude = next(c for c in result["changes"] if c["target"].endswith(".claude.json"))
        self.assertEqual(claude["action"], "modify")
        self.assertTrue(any(d["client_config"].endswith(".claude.json") and d["present"] for d in result["discovered"]))
        self.assertEqual((self.home / ".claude.json").read_text(encoding="utf-8"), self.foreign)
        self.assertFalse(self.data.exists() and any(self.data.rglob("receipts")))
        self.assertFalse(self.vault.exists())

    def test_nothing_desired_means_no_changes_and_bad_input_is_typed(self):
        self.assertEqual(self.plan({})["result"]["changes"], [])
        self.assertEqual(self.plan({"bogus": True})["error"]["code"], "BAD_REQUEST")
        self.assertEqual(self.plan({"mcp": "yes"})["error"]["code"], "BAD_REQUEST")
        self.assertEqual(self.plan({"mcp": True}, vault_path="relative")["error"]["code"], "BAD_REQUEST")

    def test_an_unknown_respected_entry_is_reported_as_a_conflict_not_overwritten(self):
        bad = {"mcpServers": {"respected-vault": {"command": "not-ours", "args": []}}}
        (self.home / ".claude.json").write_text(json.dumps(bad), encoding="utf-8")
        response = self.plan({"mcp": True})
        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "LIFECYCLE_CONFLICT")
        self.assertEqual(json.loads((self.home / ".claude.json").read_text(encoding="utf-8")), bad)

    def test_switching_off_an_owned_entry_is_planned_as_a_restore_and_user_edits_are_conflicts(self):
        import base64
        path = self.home / ".claude.json"
        after = json.dumps({"mcpServers": {"someone-elses": {"command": "x", "args": []}, "respected-vault": {"command": "ours", "args": []}}})
        path.write_text(after, encoding="utf-8")
        self.data.mkdir(parents=True, exist_ok=True)
        encode = lambda text: base64.b64encode(text.encode("utf-8")).decode("ascii")
        manifest = {"schema_version": 3, "files": [], "external": [{"kind": "mcp", "key": str(path), "before": encode(self.foreign), "after": encode(after)}]}
        (self.data / "install-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        response = self.plan({})
        self.assertTrue(response["ok"], response)
        restore = [c for c in response["result"]["changes"] if c["action"] == "restore"]
        self.assertEqual([c["target"] for c in restore], [str(path)])
        self.assertEqual(path.read_text(encoding="utf-8"), after)
        path.write_text(after.replace('"ours"', '"edited-by-user"'), encoding="utf-8")
        self.assertEqual(self.plan({})["error"]["code"], "LIFECYCLE_CONFLICT")
        # a client rewriting the file elsewhere (not our entry) is NOT a conflict (audit P0 #1)
        path.write_text(json.dumps({"counter": 7, **json.loads(after)}), encoding="utf-8")
        self.assertTrue(self.plan({})["ok"])

    def test_clients_limit_the_plan_to_the_selected_ai_tools(self):
        everything = self.plan({"global": True, "mcp": True})["result"]
        only = self.plan({"global": True, "mcp": True, "clients": ["claude"]})["result"]
        targets = [c["target"].replace("\\", "/") for c in only["changes"]]
        self.assertTrue(targets and all("/.claude" in t or "/plugin/" in t for t in targets), targets)
        self.assertFalse(any("/.codex/" in t or "/.gemini/" in t for t in targets), targets)
        self.assertGreater(len(everything["changes"]), len(only["changes"]))
        self.assertEqual(only["desired"]["clients"], ["claude"])
        detected = {c["id"]: c["detected"] for c in only["clients"]}
        self.assertTrue(detected["claude"] and detected["gemini"] and not detected["codex"])
        self.assertEqual(self.plan({"mcp": True, "clients": ["nope"]})["error"]["code"], "BAD_REQUEST")
        self.assertEqual(self.plan({"global": True, "clients": []})["result"]["changes"], [])

    def test_what_is_already_installed_and_still_wanted_is_not_a_restore(self):
        # the preview of the stored choice must say "nothing changes", not "everything returns to its old state"
        import base64
        codex = self.home / ".codex/hooks.json"
        codex.parent.mkdir(parents=True)
        codex.write_text('{"owned": true}', encoding="utf-8")
        self.data.mkdir(parents=True, exist_ok=True)
        encode = lambda text: base64.b64encode(text.encode("utf-8")).decode("ascii")
        manifest = {"schema_version": 3, "files": [], "external": [{"kind": "file", "key": str(codex), "before": encode("{}"), "after": encode('{"owned": true}')}]}
        (self.data / "install-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

        def still_wanted_and_up_to_date(ctx, profile, desired, backend, planned_keys=None):
            planned_keys.add(("file", str(codex)))   # planned, but the file already has this content: no change row
            return ()
        with patch("respected_brain.integrations.rendering.plan_integrations", still_wanted_and_up_to_date):
            changes = self.plan({"global": True, "clients": ["codex"]})["result"]["changes"]
        self.assertEqual(changes, [])

    def test_deselecting_a_client_plans_a_restore_of_its_owned_files(self):
        import base64
        codex = self.home / ".codex/hooks.json"
        codex.parent.mkdir(parents=True)
        codex.write_text('{"owned": true}', encoding="utf-8")
        self.data.mkdir(parents=True, exist_ok=True)
        encode = lambda text: base64.b64encode(text.encode("utf-8")).decode("ascii")
        manifest = {"schema_version": 3, "files": [], "external": [{"kind": "file", "key": str(codex), "before": encode("{}"), "after": encode('{"owned": true}')}]}
        (self.data / "install-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        kept = self.plan({"global": True, "clients": ["codex"]})["result"]["changes"]
        self.assertFalse(any(c["action"] == "restore" for c in kept))
        dropped = self.plan({"global": True, "clients": ["claude"]})["result"]["changes"]
        self.assertEqual([c["target"] for c in dropped if c["action"] == "restore"], [str(codex)])
        self.assertEqual(codex.read_text(encoding="utf-8"), '{"owned": true}')

if __name__ == "__main__":
    unittest.main()
