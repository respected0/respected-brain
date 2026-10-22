"""RPP memory.write / memory.write.revert through rpp.serve (temporary directories only)."""

from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from uuid import uuid4

from respected_brain.rpp import server as rpp
from respected_brain.core.config import ConfigStore


class MemoryWriteTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="rpp-memwrite-")
        self.addCleanup(temporary.cleanup)
        base = Path(temporary.name).resolve()
        self.data, self.vault = base / "data", base / "vault"
        self.data.mkdir()
        self.vault.mkdir()
        (self.vault / "keep.md").write_text("# Keep\nuser note\n", encoding="utf-8")
        patcher = patch.dict(os.environ, {"RESPECTED_APP_DIR": str(base / "app"), "RESPECTED_DATA_DIR": str(self.data)})
        patcher.start()
        self.addCleanup(patcher.stop)

        def mutate(document):
            vault_id = str(uuid4())
            document["vaults"][vault_id] = {"path": str(self.vault)}
            document["active_vault_id"] = vault_id
        ConfigStore(self.data).update(mutate)

    def call(self, op, payload, operation_id=None):
        request = {"rpp": "1", "op": op, "payload": payload}
        if operation_id:
            request["operation_id"] = operation_id
        return rpp.serve(json.dumps(request), data_root=str(self.data))

    def token(self, write=True, op="op-grant-0001"):
        response = self.call("memory.grant", {"label": "orch", "write": write}, op)
        self.assertTrue(response["ok"], response)
        return response["result"]["token"]

    def write(self, token, op="op-write-0001", **extra):
        return self.call("memory.write", {"token": token, "title": "Decision: use SQLite", "body": "We chose SQLite.", **extra}, op)

    def test_write_creates_new_note_only_in_inbox_and_recall_finds_it(self):
        token = self.token()
        before = {p: p.read_bytes() for p in self.vault.rglob("*") if p.is_file()}
        reply = self.write(token, tags=["decision"])
        self.assertTrue(reply["ok"], reply)
        note = self.vault / reply["result"]["path"]
        self.assertTrue(note.is_file())
        self.assertIn("source: orchestrator", note.read_text(encoding="utf-8"))
        self.assertEqual({p: p.read_bytes() for p in before}, before)  # nothing existing changed
        self.assertTrue(reply["result"]["indexed"])
        found = self.call("memory.recall", {"token": token, "query": "SQLite"})
        self.assertEqual(found["result"]["count"], 1)

    def test_read_only_and_unknown_tokens_are_denied(self):
        for token in (self.token(write=False), "rbm_nope"):
            reply = self.write(token)
            self.assertFalse(reply["ok"])
            self.assertEqual(reply["error"]["code"], "PERMISSION_DENIED")
        self.assertFalse((self.vault / "🔮 850-Companion").exists())

    def test_idempotent_and_conflicting_operation_id(self):
        token = self.token()
        first = self.write(token)
        again = self.write(token)
        self.assertTrue(again["result"]["replayed"])
        self.assertEqual(first["result"]["path"], again["result"]["path"])
        clash = self.call("memory.write", {"token": token, "title": "Other", "body": "x"}, "op-write-0001")
        self.assertEqual(clash["error"]["code"], "OPERATION_ID_CONFLICT")

    def test_paths_and_oversize_are_rejected(self):
        token = self.token()
        self.assertEqual(self.write(token, path="../x.md")["error"]["code"], "BAD_REQUEST")
        big = self.call("memory.write", {"token": token, "title": "t", "body": "x" * 20_001}, "op-write-0002")
        self.assertEqual(big["error"]["code"], "BAD_REQUEST")

    def test_revert_removes_untouched_note_and_refuses_edited_one(self):
        token = self.token()
        path = self.vault / self.write(token)["result"]["path"]
        done = self.call("memory.write.revert", {"token": token, "operation_id": "op-write-0001"})
        self.assertTrue(done["result"]["reverted"])
        self.assertFalse(path.exists())
        path = self.vault / self.write(token, op="op-write-0003")["result"]["path"]
        path.write_text(path.read_text(encoding="utf-8") + "user edit\n", encoding="utf-8")
        refused = self.call("memory.write.revert", {"token": token, "operation_id": "op-write-0003"})
        self.assertEqual(refused["error"]["code"], "NOTE_CHANGED")
        self.assertTrue(path.exists())

if __name__ == "__main__":
    unittest.main()
