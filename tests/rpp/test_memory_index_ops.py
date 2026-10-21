"""RPP memory.index.* ops end to end through rpp.serve (temporary directories only)."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from uuid import uuid4

from respectedbrain.rpp import server as rpp
from respectedbrain.core.config import ConfigStore

OPS = ["memory.index.status", "memory.index.refresh"]
OLD_TEXT = "The zebra crosses the road."
NEW_TEXT = "The zebra gallops across the meadow quickly."


def snapshot(root: Path) -> dict:
    """Relative path -> (size, mtime_ns, sha256) for every file under root."""
    state = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            info = path.stat()
            state[path.relative_to(root).as_posix()] = (
                info.st_size, info.st_mtime_ns, hashlib.sha256(path.read_bytes()).hexdigest())
    return state


class MemoryIndexOpTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="rpp-memidx-")
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name).resolve()
        self.data, self.vault = self.base / "data", self.base / "vault"
        self.data.mkdir()
        (self.vault / "notes").mkdir(parents=True)
        self.note = self.vault / "notes" / "zebra.md"
        self.note.write_text(f"# Zebra\n{OLD_TEXT}\n", encoding="utf-8")
        patcher = patch.dict(os.environ, {"RESPECTED_APP_DIR": str(self.base / "app"),
                                          "RESPECTED_DATA_DIR": str(self.data)})
        patcher.start()
        self.addCleanup(patcher.stop)

        def mutate(document):
            vault_id = str(uuid4())
            document["vaults"][vault_id] = {"path": str(self.vault)}
            document["active_vault_id"] = vault_id
        ConfigStore(self.data).update(mutate)

    def call(self, op, payload=None, version="1.1", operation_id=None):
        request = {"rpp": version, "op": op}
        if payload is not None:
            request["payload"] = payload
        if operation_id is not None:
            request["operation_id"] = operation_id
        return rpp.serve(json.dumps(request), data_root=str(self.data))

    def refresh(self, operation_id="op-refresh-0001", payload=None):
        return self.call("memory.index.refresh", payload or {"confirm": True}, operation_id=operation_id)

    def test_ops_require_protocol_11(self):
        for op in OPS:
            response = self.call(op, {"confirm": True}, version="1.0", operation_id="op-refresh-0001")
            self.assertFalse(response["ok"])
            self.assertEqual(response["error"]["code"], "UNSUPPORTED_OP")

    def test_manifest_capability_visibility(self):
        old = self.call("manifest", version="1.0")["result"]
        self.assertNotIn("memory_index", old["capabilities"])
        new = self.call("manifest")["result"]
        self.assertIn("memory_index", new["capabilities"])
        detail = {item["id"]: item for item in new["capability_details"]}["memory_index"]
        self.assertEqual((detail["since"], detail["ops"]), ("1.1", OPS))

    def test_unknown_op_hint_lists_index_ops(self):
        response = self.call("nope")
        self.assertEqual(response["error"]["code"], "UNKNOWN_OP")
        for op in OPS:
            self.assertIn(op, response["error"]["hint"])

    def test_refresh_rejects_bad_requests(self):
        cases = [
            ({"confirm": True}, None),  # no operation id
            ({}, "op-refresh-0001"),  # no confirm
            ({"confirm": True, "path": "/tmp/x"}, "op-refresh-0001"),  # extra key
        ]
        for payload, operation_id in cases:
            response = self.call("memory.index.refresh", payload, operation_id=operation_id)
            self.assertFalse(response["ok"], payload)
            self.assertEqual(response["error"]["code"], "BAD_REQUEST", payload)

    def test_status_refresh_status_flow_and_replay(self):
        before = self.call("memory.index.status")
        self.assertTrue(before["ok"], before)
        self.assertEqual(before["result"]["index"]["state"], "missing")
        self.assertIsNone(before["result"]["last_refresh"])

        first = self.refresh()
        self.assertTrue(first["ok"], first)
        self.assertFalse(first["result"]["replayed"])
        self.assertEqual(first["result"]["indexed"], 1)
        self.assertEqual(first["result"]["index"]["state"], "fresh")

        after = self.call("memory.index.status")["result"]
        self.assertEqual(after["index"]["state"], "fresh")
        self.assertEqual(after["last_refresh"]["operation_id"], "op-refresh-0001")

        replay = self.refresh()
        self.assertTrue(replay["ok"], replay)
        self.assertTrue(replay["result"]["replayed"])

    def test_refresh_leaves_vault_unchanged(self):
        before = snapshot(self.vault)
        self.assertTrue(self.refresh()["ok"])
        self.assertEqual(snapshot(self.vault), before)

    def test_recall_sees_new_text_only_after_refresh(self):
        self.assertTrue(self.refresh()["ok"])
        granted = self.call("memory.grant", {"label": "orchestrator"}, operation_id="op-grant-0001")
        self.assertTrue(granted["ok"], granted)
        token = granted["result"]["token"]

        self.note.write_text(f"# Zebra\n{NEW_TEXT}\n", encoding="utf-8")
        stale = self.call("memory.recall", {"token": token, "query": "zebra"})
        self.assertTrue(stale["ok"], stale)
        self.assertNotIn("crosses the road", json.dumps(stale))

        self.assertTrue(self.refresh("op-refresh-0002")["ok"])
        fresh = self.call("memory.recall", {"token": token, "query": "zebra"})
        self.assertTrue(fresh["ok"], fresh)
        self.assertIn("gallops", json.dumps(fresh))
        self.assertNotIn("crosses the road", json.dumps(fresh))

    def test_earlier_ops_still_answer(self):
        self.assertTrue(self.call("health", version="1.0")["ok"])
        self.assertTrue(self.call("settings.schema", version="1.0")["ok"])
        readback = self.call("settings.readback", version="1.0")
        self.assertTrue(readback["ok"])
        self.assertIn("summary_provider", readback["result"]["settings"])
        denied = self.call("memory.recall", {"token": "x" * 40, "query": "zebra"})
        self.assertEqual(denied["error"]["code"], "PERMISSION_DENIED")


if __name__ == "__main__":
    unittest.main()
