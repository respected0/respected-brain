"""RPP memory.* ops end to end through rpp.serve (temporary directories only)."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from uuid import uuid4

from respected_brain.rpp import server as rpp
from respected_brain.core.config import ConfigStore
from respected_brain.rpp.integrations import _context
from respected_brain.search.engine import SearchEngine

OPS = ["memory.grant", "memory.revoke", "memory.recall"]


def snapshot(root: Path) -> dict:
    """Relative path -> (size, mtime_ns, sha256) for every file under root."""
    state = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            info = path.stat()
            state[path.relative_to(root).as_posix()] = (
                info.st_size, info.st_mtime_ns, hashlib.sha256(path.read_bytes()).hexdigest())
    return state


class MemoryOpTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="rpp-memop-")
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name).resolve()
        self.data, self.vault = self.base / "data", self.base / "vault"
        self.data.mkdir()
        (self.vault / "notes").mkdir(parents=True)
        (self.vault / "notes" / "zebra.md").write_text("# Zebra\nThe zebra crosses the road.\n", encoding="utf-8")
        patcher = patch.dict(os.environ, {"RESPECTED_APP_DIR": str(self.base / "app"),
                                          "RESPECTED_DATA_DIR": str(self.data)})
        patcher.start()
        self.addCleanup(patcher.stop)

        def mutate(document):
            vault_id = str(uuid4())
            document["vaults"][vault_id] = {"path": str(self.vault)}
            document["active_vault_id"] = vault_id
        ConfigStore(self.data).update(mutate)
        _, ctx = _context(self.data, {})
        SearchEngine(ctx).index_vault()

    def call(self, op, payload=None, version="1", operation_id=None):
        request = {"rpp": version, "op": op}
        if payload is not None:
            request["payload"] = payload
        if operation_id is not None:
            request["operation_id"] = operation_id
        return rpp.serve(json.dumps(request), data_root=str(self.data))

    def grant(self, operation_id="op-grant-0001"):
        response = self.call("memory.grant", {"label": "orchestrator"}, operation_id=operation_id)
        self.assertTrue(response["ok"], response)
        return response["result"]

    def test_rpp_responses_never_carry_the_token_hash(self):
        granted = self.call("memory.grant", {"label": "orchestrator"}, operation_id="op-grant-0001")
        revoked = self.call("memory.revoke", {"grant_id": granted["result"]["grant_id"]}, operation_id="op-revoke-0001")
        for response in (granted, revoked):
            self.assertTrue(response["ok"], response)
            self.assertNotIn("token_sha256", json.dumps(response))
        self.assertNotIn(granted["result"]["token"], json.dumps(revoked))

    def test_unknown_op_hint_lists_memory_ops(self):
        response = self.call("nope")
        self.assertEqual(response["error"]["code"], "UNKNOWN_OP")
        for op in OPS:
            self.assertIn(op, response["error"]["hint"])

    def test_recall_without_grant_is_denied(self):
        response = self.call("memory.recall", {"token": "x" * 40, "query": "zebra"})
        self.assertFalse(response["ok"])
        self.assertEqual(response["error"]["code"], "PERMISSION_DENIED")

    def test_grant_requires_operation_id(self):
        response = self.call("memory.grant", {"label": "orchestrator"})
        self.assertEqual(response["error"]["code"], "BAD_REQUEST")

    def test_grant_recall_replay_and_revoke(self):
        granted = self.grant()
        token = granted["token"]
        response = self.call("memory.recall", {"token": token, "query": "zebra"})
        self.assertTrue(response["ok"], response)
        self.assertTrue(response["result"]["read_only"])
        self.assertEqual(response["result"]["count"], 1)
        self.assertEqual(response["result"]["results"][0]["path"], "notes/zebra.md")

        replay = self.call("memory.grant", {"label": "orchestrator"}, operation_id="op-grant-0001")
        self.assertEqual(replay["error"]["code"], "GRANT_EXISTS")

        revoked = self.call("memory.revoke", {"grant_id": granted["grant_id"]})
        self.assertTrue(revoked["ok"], revoked)
        after = self.call("memory.recall", {"token": token, "query": "zebra"})
        self.assertEqual(after["error"]["code"], "PERMISSION_DENIED")

    def test_earlier_ops_still_answer(self):
        self.assertTrue(self.call("health", version="1")["ok"])
        self.assertTrue(self.call("settings.schema", version="1")["ok"])
        readback = self.call("settings.readback", version="1")
        self.assertTrue(readback["ok"])
        self.assertIn("summary_provider", readback["result"]["settings"])

    def test_recall_leaves_data_root_and_vault_unchanged(self):
        token = self.grant()["token"]
        before = (snapshot(self.data), snapshot(self.vault))
        response = self.call("memory.recall", {"token": token, "query": "zebra"})
        self.assertTrue(response["ok"], response)
        self.assertEqual((snapshot(self.data), snapshot(self.vault)), before)


if __name__ == "__main__":
    unittest.main()
