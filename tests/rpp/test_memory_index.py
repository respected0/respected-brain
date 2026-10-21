"""rpp_memory_index: confirmed index refresh and read-only status (temporary directories only)."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from uuid import uuid4

from respectedbrain.rpp import memory as rpp_memory, memory_index as idx
from respectedbrain.core.config import ConfigStore
from respectedbrain.rpp.integrations import _context
from respectedbrain.search.engine import SearchEngine


def snapshot(*roots: Path) -> dict:
    """(root, relative path) -> (size, mtime_ns, sha256) for every file under the roots."""
    state = {}
    for root in roots:
        for path in sorted(root.rglob("*")):
            if path.is_file():
                info = path.stat()
                state[(str(root), path.relative_to(root).as_posix())] = (
                    info.st_size, info.st_mtime_ns, hashlib.sha256(path.read_bytes()).hexdigest())
    return state


class MemoryIndexTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="rpp-idx-")
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name).resolve()
        self.data, self.vault = self.base / "data", self.base / "vault"
        self.data.mkdir()
        (self.vault / "notes").mkdir(parents=True)
        (self.vault / "notes" / "zebra.md").write_text("# Zebra\nThe zebra crosses the road slowly.\n", encoding="utf-8")
        (self.vault / "notes" / "zebra2.md").write_text("# Zebra two\nAnother zebra story.\n", encoding="utf-8")
        (self.vault / "giraffe.md").write_text("# Giraffe\nA tall giraffe and a zebra.\n", encoding="utf-8")
        patcher = patch.dict(os.environ, {"RESPECTED_APP_DIR": str(self.base / "app"), "RESPECTED_DATA_DIR": str(self.data)})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.vault_id = str(uuid4())
        self.register(self.vault_id)

    def register(self, vault_id):
        def mutate(document):
            document["vaults"][vault_id] = {"path": str(self.vault)}
            document["active_vault_id"] = vault_id
        ConfigStore(self.data).update(mutate)

    def refresh(self, name="op-refresh-0001", **payload):
        return idx.refresh(self.data, name, {"confirm": True, **payload})

    def assertCode(self, code, function, *args):
        with self.assertRaises(idx.MemoryIndexError) as caught:
            function(*args)
        self.assertEqual(caught.exception.code, code)
        return caught.exception

    def edit(self, relative, text):
        path = self.vault / relative
        path.write_text(text, encoding="utf-8")
        stamp = path.stat().st_mtime + 10  # guarantee a different mtime
        os.utime(path, (stamp, stamp))

    def recall(self, token, query):
        return rpp_memory.recall(self.data, {"token": token, "query": query, "limit": 20})["results"]

    def test_status_without_index_is_missing_and_writes_nothing(self):
        before = snapshot(self.data, self.vault)
        report = idx.status(self.data)
        self.assertEqual(report["vault_id"], self.vault_id)
        self.assertEqual(report["index"]["state"], "missing")
        self.assertIsNone(report["index"]["indexed_files"])
        self.assertIsNone(report["last_refresh"])
        self.assertEqual(snapshot(self.data, self.vault), before)
        self.assertFalse((self.data / "memory-index-refresh.json").exists())
        self.assertFalse((self.data / "memory-index-operations").exists())

    def test_refresh_builds_index_and_status_becomes_fresh(self):
        result = self.refresh()
        self.assertEqual(result["indexed"], 3)
        self.assertEqual(result["total"], 3)
        self.assertFalse(result["replayed"])
        self.assertFalse(result["force"])
        self.assertEqual(result["vault_id"], self.vault_id)
        self.assertEqual(result["index"]["state"], "fresh")
        report = idx.status(self.data)
        self.assertEqual(report["index"]["state"], "fresh")
        self.assertEqual(report["index"]["indexed_files"], 3)
        self.assertEqual(report["last_refresh"]["operation_id"], "op-refresh-0001")
        self.assertEqual(report["last_refresh"]["indexed"], 3)

    def test_refresh_never_touches_the_vault_and_writes_only_own_files(self):
        _, ctx = _context(self.data, {})
        cache = ctx.paths.cache_dir.resolve()
        vault_before = snapshot(self.vault)
        data_before = snapshot(self.data)
        self.refresh()
        self.assertEqual(snapshot(self.vault), vault_before)
        changed = {key[1] for key, value in snapshot(self.data).items() if data_before.get(key) != value}
        self.assertIn("memory-index-refresh.json", changed)
        self.assertIn("memory-index-operations/op-refresh-0001.json", changed)
        for rel in changed:
            full = (self.data / rel).resolve()
            own = full.is_relative_to(cache) or rel in {"memory-index-refresh.json", "memory-index-operations/op-refresh-0001.json"}
            self.assertTrue(own or any(word in rel for word in ("lock", "lease")), rel)
        self.assertEqual(len(list((self.data / "memory-index-operations").glob("*.json"))), 1)

    def test_edit_makes_stale_then_refresh_reindexes_only_that_note(self):
        self.refresh()
        token = rpp_memory.grant(self.data, "op-grant-0001", {"label": "orchestrator"})["token"]
        self.edit("notes/zebra.md", "# Zebra\nA quokka naps in the shade.\n")
        self.assertEqual(idx.status(self.data)["index"]["state"], "stale")
        result = self.refresh("op-refresh-0002")
        self.assertEqual(result["indexed"], 1)
        self.assertEqual(result["skipped"], 2)
        self.assertEqual(idx.status(self.data)["index"]["state"], "fresh")
        self.assertIn("notes/zebra.md", {hit["path"] for hit in self.recall(token, "quokka")})
        self.assertNotIn("notes/zebra.md", {hit["path"] for hit in self.recall(token, "crosses")})

    def test_deleted_note_is_dropped_from_the_index(self):
        self.refresh()
        (self.vault / "giraffe.md").unlink()
        result = self.refresh("op-refresh-0002")
        self.assertEqual(result["deleted"], 1)
        self.assertEqual(result["total"], 2)

    def test_validation_matrix(self):
        for payload in ({}, {"force": True}, {"confirm": False}, {"confirm": "true"}, {"confirm": 1}):
            error = self.assertCode("BAD_REQUEST", idx.refresh, self.data, "op-refresh-0001", payload)
            self.assertEqual(error.message, "explicit confirmation required")
        for extra in ("vault_path", "path", "host", "vault_id"):
            error = self.assertCode("BAD_REQUEST", idx.refresh, self.data, "op-refresh-0001", {"confirm": True, extra: "x"})
            self.assertIn("paths and identities are not accepted", error.message)
        self.assertCode("BAD_REQUEST", idx.refresh, self.data, "op-refresh-0001", "confirm")
        for bad_id in ("short", "x" * 65, "bad id/../1", "", None, 12345678):
            self.assertCode("BAD_REQUEST", idx.refresh, self.data, bad_id, {"confirm": True})
        for force in ("yes", 1, None):
            self.assertCode("BAD_REQUEST", idx.refresh, self.data, "op-refresh-0001", {"confirm": True, "force": force})
        self.assertFalse((self.data / "memory-index-operations").exists())

    def test_force_flag_is_forwarded(self):
        result = self.refresh(force=True)
        self.assertTrue(result["force"])
        self.assertEqual(result["indexed"], 3)

    def test_replay_does_not_run_again_and_conflict_is_rejected(self):
        stats = {"indexed": 3, "skipped": 0, "deleted": 0, "total": 3}
        with patch.object(SearchEngine, "index_vault", return_value=stats) as mocked:
            first = self.refresh()
            again = self.refresh()
            self.assertEqual(mocked.call_count, 1)
            self.assertCode("OPERATION_ID_CONFLICT", idx.refresh, self.data, "op-refresh-0001", {"confirm": True, "force": True})
            self.assertEqual(mocked.call_count, 1)
        self.assertFalse(first["replayed"])
        self.assertTrue(again["replayed"])
        self.assertEqual({k: v for k, v in again.items() if k != "replayed"}, {k: v for k, v in first.items() if k != "replayed"})

    def test_busy_writer_stores_no_record(self):
        with patch.object(SearchEngine, "index_vault", return_value=None):
            error = self.assertCode("INDEX_BUSY", idx.refresh, self.data, "op-refresh-0001", {"confirm": True})
        self.assertIn("try again shortly", error.hint)
        self.assertFalse((self.data / "memory-index-operations" / "op-refresh-0001.json").exists())
        self.assertFalse((self.data / "memory-index-refresh.json").exists())

    def test_no_vault_registered(self):
        def mutate(document):
            document["active_vault_id"] = None
            document["vaults"].clear()
        ConfigStore(self.data).update(mutate)
        self.assertCode("NO_VAULT", idx.status, self.data)
        self.assertCode("NO_VAULT", idx.refresh, self.data, "op-refresh-0001", {"confirm": True})

    def test_operation_records_keep_only_the_newest_fifty(self):
        stats = {"indexed": 0, "skipped": 3, "deleted": 0, "total": 3}
        with patch.object(SearchEngine, "index_vault", return_value=stats):
            for number in range(51):
                self.refresh(f"op-refresh-{number:04d}")
        names = {path.name for path in (self.data / "memory-index-operations").glob("*.json")}
        self.assertEqual(len(names), 50)
        self.assertNotIn("op-refresh-0000.json", names)
        self.assertIn("op-refresh-0050.json", names)
        record = json.loads((self.data / "memory-index-operations" / "op-refresh-0050.json").read_text(encoding="utf-8"))
        self.assertEqual(set(record) & {"payload_sha256", "result"}, {"payload_sha256", "result"})

    def test_status_never_writes(self):
        self.refresh()
        self.edit("giraffe.md", "# Giraffe\nChanged.\n")
        before = snapshot(self.data, self.vault)
        idx.status(self.data)
        self.assertEqual(snapshot(self.data, self.vault), before)


if __name__ == "__main__":
    unittest.main()
