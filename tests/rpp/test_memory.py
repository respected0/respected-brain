"""rpp_memory: read-only memory recall behind explicit grants (temporary directories only)."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
from uuid import uuid4

from respected_brain.rpp import memory as rpp_memory
from respected_brain.core.config import ConfigStore
from respected_brain.rpp.integrations import _context
from respected_brain.search.engine import SearchEngine


def snapshot(*roots: Path) -> dict:
    """Relative path -> (size, mtime_ns, sha256) for every file under the roots."""
    state = {}
    for root in roots:
        for path in sorted(root.rglob("*")):
            if path.is_file():
                info = path.stat()
                state[(str(root), path.relative_to(root).as_posix())] = (
                    info.st_size, info.st_mtime_ns, hashlib.sha256(path.read_bytes()).hexdigest())
    return state


class MemoryRecallTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="rpp-mem-")
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name).resolve()
        self.data, self.vault = self.base / "data", self.base / "vault"
        self.data.mkdir()
        (self.vault / "notes").mkdir(parents=True)
        (self.vault / "notes" / "zebra.md").write_text("# Zebra\nThe zebra crosses\tthe road\nslowly.\n", encoding="utf-8")
        (self.vault / "notes" / "zebra2.md").write_text("# Zebra two\nAnother zebra story.\n", encoding="utf-8")
        (self.vault / "giraffe.md").write_text("# Giraffe\nA tall giraffe and a zebra.\n", encoding="utf-8")
        patcher = patch.dict(os.environ, {"RESPECTED_APP_DIR": str(self.base / "app"), "RESPECTED_DATA_DIR": str(self.data)})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.vault_id = str(uuid4())
        self.register(self.vault_id)

    def register(self, vault_id, path=None):
        def mutate(document):
            document["vaults"][vault_id] = {"path": str(path or self.vault)}
            document["active_vault_id"] = vault_id
        ConfigStore(self.data).update(mutate)

    def build_index(self):
        _, ctx = _context(self.data, {})
        SearchEngine(ctx).index_vault()
        return ctx

    def make_grant(self, name="op-grant-0001", **payload):
        return rpp_memory.grant(self.data, name, {"label": "orchestrator", **payload})

    def recall(self, token, **payload):
        return rpp_memory.recall(self.data, {"token": token, "query": "zebra", **payload})

    def assertCode(self, code, function, *args):
        with self.assertRaises(rpp_memory.MemoryOpError) as caught:
            function(*args)
        self.assertEqual(caught.exception.code, code)
        return caught.exception

    def test_every_returned_text_field_is_bounded(self):
        (self.vault / "long.md").write_text("---\ntitle: " + "T" * 5000 + "\n---\nzebra long title note\n", encoding="utf-8")
        self.build_index()
        token = self.make_grant()["token"]
        for row in self.recall(token, limit=20)["results"]:
            self.assertLessEqual(len(row["title"]), 200)
            self.assertLessEqual(len(row["category"]), 64)
            self.assertLessEqual(len(row["tags"]), 200)
            self.assertLessEqual(len(row["snippet"]), 203)

    def test_grant_then_recall_returns_bounded_snippets(self):
        self.build_index()
        granted = self.make_grant()
        self.assertEqual(granted["vault_id"], self.vault_id)
        result = self.recall(granted["token"], limit=10, snippet_chars=40)
        self.assertTrue(result["read_only"])
        self.assertEqual(result["grant_id"], "op-grant-0001")
        self.assertEqual(result["vault_id"], self.vault_id)
        self.assertEqual(result["count"], 3)
        self.assertEqual(result["dropped"], 0)
        self.assertEqual(result["index"]["state"], "fresh")
        for hit in result["results"]:
            self.assertEqual(set(hit), {"path", "title", "category", "tags", "snippet", "score"})
            self.assertLessEqual(len(hit["snippet"]), 43)
            for marker in (">>>", "<<<", "\n", "\t"):
                self.assertNotIn(marker, hit["snippet"])
        self.assertIn("giraffe.md", {hit["path"] for hit in result["results"]})

    def test_results_never_contain_absolute_paths(self):
        self.build_index()
        result = self.recall(self.make_grant()["token"], limit=10)
        for hit in result["results"]:
            self.assertFalse(Path(hit["path"]).is_absolute())
            self.assertNotIn("\\", hit["path"])
            self.assertNotIn("..", hit["path"].split("/"))
            self.assertFalse(hit["path"].startswith(str(self.base)))

    def test_missing_wrong_or_revoked_token_is_denied_and_touches_nothing(self):
        self.build_index()
        granted = self.make_grant()
        self.assertCode("BAD_REQUEST", rpp_memory.recall, self.data, {"query": "zebra"})
        wrong = self.assertCode("PERMISSION_DENIED", rpp_memory.recall, self.data, {"token": "rbm_nope", "query": "zebra"})
        self.assertEqual(rpp_memory.revoke(self.data, {"grant_id": "op-grant-0001"})["revoked"], True)
        after_revoke = snapshot(self.vault, self.data)
        revoked = self.assertCode("PERMISSION_DENIED", self.recall, granted["token"])
        self.assertEqual(wrong.message, revoked.message)
        self.assertEqual(snapshot(self.vault, self.data), after_revoke)

    def test_payload_validation_matrix(self):
        token = "rbm_whatever"
        before = snapshot(self.vault, self.data)
        for key in ("vault_path", "path", "root", "host", "consumer"):
            error = self.assertCode("BAD_REQUEST", rpp_memory.recall, self.data, {"token": token, "query": "zebra", key: "x"})
            self.assertIn("not accepted", error.message)
        bad = [
            {"query": ""}, {"query": "   "}, {"query": "a" * 201}, {"query": " ".join(["w"] * 13)},
            {"query": "!!!"}, {"query": 5},
            {"limit": 0}, {"limit": 21}, {"limit": True}, {"limit": "5"},
            {"snippet_chars": 39}, {"snippet_chars": 401},
            {"category": ""}, {"category": "a/b"}, {"category": "a\\b"}, {"category": "a..b"},
            {"category": "x" * 65}, {"category": 3},
        ]
        for extra in bad:
            payload = {"token": token, "query": "zebra", **extra}
            self.assertCode("BAD_REQUEST", rpp_memory.recall, self.data, payload)
        self.assertCode("BAD_REQUEST", rpp_memory.recall, self.data, "nope")
        self.assertEqual(snapshot(self.vault, self.data), before)

    def test_twelve_terms_are_accepted(self):
        self.build_index()
        token = self.make_grant()["token"]
        self.assertEqual(self.recall(token, query=" ".join(["zebra"] * 12))["count"], 3)

    def test_grant_requires_operation_id_and_an_active_vault(self):
        self.assertCode("BAD_REQUEST", rpp_memory.grant, self.data, None, {"label": "x"})
        self.assertCode("BAD_REQUEST", rpp_memory.grant, self.data, "op-grant-0001", {"label": "x", "vault_path": "y"})
        with tempfile.TemporaryDirectory(prefix="rpp-mem-empty-") as empty:
            with patch.dict(os.environ, {"RESPECTED_DATA_DIR": empty}):
                self.assertCode("NO_VAULT", rpp_memory.grant, Path(empty).resolve(), "op-grant-0002", {"label": "x"})

    def test_deleted_file_is_dropped_and_index_is_stale(self):
        self.build_index()
        token = self.make_grant()["token"]
        (self.vault / "giraffe.md").unlink()
        result = self.recall(token, limit=10)
        self.assertEqual(result["dropped"], 1)
        self.assertEqual(result["count"], 2)
        self.assertNotIn("giraffe.md", {hit["path"] for hit in result["results"]})
        self.assertEqual(result["index"]["state"], "stale")

    def bump_mtime(self, path):
        info = path.stat()
        os.utime(path, ns=(info.st_atime_ns, info.st_mtime_ns + 10_000_000_000))

    def test_edited_note_old_text_is_not_returned(self):
        (self.vault / "secret.md").write_text("# Secret\nthe passphrase quokkasecret is here\n", encoding="utf-8")
        self.build_index()
        token = self.make_grant()["token"]
        note = self.vault / "secret.md"
        note.write_text("# Secret\nnothing sensitive remains\n", encoding="utf-8")
        self.bump_mtime(note)
        result = self.recall(token, query="quokkasecret")
        self.assertEqual(result["results"], [])
        self.assertEqual(result["count"], 0)
        self.assertEqual(result["dropped_stale"], 1)
        self.assertEqual(result["dropped"], 0)
        self.assertEqual(result["index"]["state"], "stale")
        self.assertNotIn("quokkasecret", repr(result))

    def test_edited_note_still_matching_is_dropped_but_untouched_is_returned(self):
        self.build_index()
        token = self.make_grant()["token"]
        note = self.vault / "notes" / "zebra.md"
        note.write_text("# Zebra\nThe zebra now says something else entirely.\n", encoding="utf-8")
        self.bump_mtime(note)
        result = self.recall(token, limit=10)
        paths = {hit["path"] for hit in result["results"]}
        self.assertNotIn("notes/zebra.md", paths)
        self.assertEqual(paths, {"notes/zebra2.md", "giraffe.md"})
        self.assertEqual(result["dropped_stale"], 1)
        self.assertEqual(result["count"], 2)

    def test_touched_note_with_same_bytes_is_still_returned(self):
        self.build_index()
        token = self.make_grant()["token"]
        self.bump_mtime(self.vault / "giraffe.md")
        result = self.recall(token, limit=10)
        self.assertEqual(result["count"], 3)
        self.assertEqual(result["dropped_stale"], 0)
        self.assertIn("giraffe.md", {hit["path"] for hit in result["results"]})

    def test_stale_drop_changes_nothing(self):
        self.build_index()
        token = self.make_grant()["token"]
        note = self.vault / "giraffe.md"
        note.write_text("# Giraffe\nzebra rewritten\n", encoding="utf-8")
        before = snapshot(self.vault, self.data)
        self.assertEqual(self.recall(token, limit=10)["dropped_stale"], 1)
        self.assertEqual(snapshot(self.vault, self.data), before)

    def test_missing_index_creates_nothing(self):
        token = self.make_grant()["token"]
        before = snapshot(self.vault, self.data)
        self.assertCode("INDEX_MISSING", self.recall, token)
        self.assertEqual(snapshot(self.vault, self.data), before)
        self.assertFalse((self.data / "vaults").exists())

    def test_index_that_is_a_symlink_to_outside_the_data_root_is_refused(self):
        ctx = self.build_index()
        token = self.make_grant()["token"]
        db = ctx.paths.cache_dir / "search_index.db"
        outside = self.base / "outside.db"
        shutil.move(str(db), str(outside))
        try:
            os.symlink(outside, db)
        except (OSError, NotImplementedError, AttributeError):
            self.skipTest("symlinks cannot be created on this platform")
        self.assertCode("INDEX_INVALID", self.recall, token)

    def test_recall_leaves_vault_and_data_root_byte_and_mtime_identical(self):
        self.build_index()
        token = self.make_grant()["token"]
        before = snapshot(self.vault, self.data)
        self.recall(token, limit=10)
        self.recall(token, category="notes")
        self.assertEqual(snapshot(self.vault, self.data), before)

    def test_grant_for_another_vault_is_denied_after_the_active_vault_changes(self):
        self.build_index()
        token = self.make_grant()["token"]
        other = self.base / "other"
        other.mkdir()
        self.register(str(uuid4()), other)
        self.assertCode("PERMISSION_DENIED", self.recall, token)

    def test_limit_is_clamped_to_the_grant_maximum(self):
        self.build_index()
        token = self.make_grant(max_results=2)["token"]
        result = self.recall(token, limit=20)
        self.assertEqual(result["limit"], 2)
        self.assertEqual(result["count"], 2)


if __name__ == "__main__":
    unittest.main()
