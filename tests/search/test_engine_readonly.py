"""Read-only SearchEngine tests: no writes, typed index errors, cheap freshness check."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest

from respectedbrain.search.engine import IndexUnavailable, SearchEngine
from tests.support.files import make_context


def tree_snapshot(*roots: Path) -> dict[str, tuple[int, int, str]]:
    """Relative path -> (size, mtime_ns, sha256) for every file and directory."""
    result: dict[str, tuple[int, int, str]] = {}
    for index, root in enumerate(roots):
        for path in sorted(root.rglob("*")):
            stat = path.stat()
            digest = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else "dir"
            result[f"{index}:{path.relative_to(root).as_posix()}"] = (stat.st_size, stat.st_mtime_ns, digest)
    return result


class SearchReadOnlyTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.vault = self.root / "vault"
        (self.vault / "knowledge").mkdir(parents=True)
        for name, body in (("alpha", "Python mimarisi ve modüller"), ("beta", "Auth cookie kararı"), ("gamma", "Genel notlar")):
            (self.vault / "knowledge" / f"{name}.md").write_text(f"# {name}\n{body}\n", encoding="utf-8")
        self.ctx = make_context(self.root, self.vault)
        self.data = self.root / "data"

    def _index(self) -> SearchEngine:
        engine = SearchEngine(self.ctx)
        engine.index_vault()
        return engine

    def test_read_only_matches_normal_search(self) -> None:
        writer = self._index()
        reader = SearchEngine.open_read_only(self.ctx)
        self.assertEqual(writer.search("python"), reader.search("python"))
        self.assertTrue(reader.search("python"))

    def test_no_writes_to_vault_or_data_root(self) -> None:
        self._index()
        before = tree_snapshot(self.vault, self.data)
        reader = SearchEngine.open_read_only(self.ctx)
        reader.search("auth")
        reader.index_state()
        self.assertEqual(before, tree_snapshot(self.vault, self.data))

    def test_missing_index_creates_nothing(self) -> None:
        before = tree_snapshot(self.vault, self.data)
        with self.assertRaises(IndexUnavailable) as caught:
            SearchEngine.open_read_only(self.ctx)
        self.assertEqual(caught.exception.code, "INDEX_MISSING")
        self.assertEqual(before, tree_snapshot(self.vault, self.data))

    def test_database_without_tables_is_invalid(self) -> None:
        db_path = self.ctx.paths.cache_dir / "search_index.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        con = sqlite3.connect(str(db_path))
        con.execute("CREATE TABLE other (x INTEGER)")
        con.commit()
        con.close()
        with self.assertRaises(IndexUnavailable) as caught:
            SearchEngine.open_read_only(self.ctx)
        self.assertEqual(caught.exception.code, "INDEX_INVALID")

    def test_connection_rejects_writes(self) -> None:
        self._index()
        reader = SearchEngine.open_read_only(self.ctx)
        with reader._get_connection() as con:
            with self.assertRaises(sqlite3.OperationalError):
                con.execute("INSERT INTO files_meta (rel_path, mtime, sha256, title, category) VALUES ('x', 1, 'h', 't', 'c')")

    def test_index_state_fresh_then_stale(self) -> None:
        self._index()
        reader = SearchEngine.open_read_only(self.ctx)
        state = reader.index_state()
        self.assertEqual(state["state"], "fresh")
        self.assertEqual(state["indexed_files"], 3)
        self.assertEqual(state["checked_files"], 3)
        self.assertEqual(state["changed_files"], 0)

        (self.vault / "knowledge" / "delta.md").write_text("# delta\nyeni\n", encoding="utf-8")
        state = reader.index_state()
        self.assertEqual(state["state"], "stale")
        self.assertEqual(state["changed_files"], 1)

    def test_index_state_stale_after_edit(self) -> None:
        self._index()
        reader = SearchEngine.open_read_only(self.ctx)
        note = self.vault / "knowledge" / "alpha.md"
        note.write_text("# alpha\ndegisti\n", encoding="utf-8")
        stat = note.stat()
        os.utime(note, ns=(stat.st_atime_ns, stat.st_mtime_ns + 10_000_000_000))
        self.assertEqual(reader.index_state()["state"], "stale")

    def test_indexed_fingerprints_returns_hash_and_ignores_unknown(self) -> None:
        self._index()
        reader = SearchEngine.open_read_only(self.ctx)
        note = self.vault / "knowledge" / "alpha.md"
        found = reader.indexed_fingerprints(["knowledge/alpha.md", "nope.md"])
        self.assertEqual(set(found), {"knowledge/alpha.md"})
        mtime, digest = found["knowledge/alpha.md"]
        self.assertEqual(digest, hashlib.sha256(note.read_bytes()).hexdigest())
        self.assertEqual(mtime, note.stat().st_mtime)
        self.assertEqual(reader.indexed_fingerprints([]), {})

    def test_indexed_fingerprints_handles_more_than_200_paths(self) -> None:
        for number in range(250):
            (self.vault / "knowledge" / f"n{number}.md").write_text(f"# n{number}\nbody {number}\n", encoding="utf-8")
        self._index()
        reader = SearchEngine.open_read_only(self.ctx)
        names = [f"knowledge/n{number}.md" for number in range(250)] + ["missing.md"]
        self.assertEqual(set(reader.indexed_fingerprints(names)), set(names[:250]))

    def test_index_state_unknown_when_truncated(self) -> None:
        self._index()
        reader = SearchEngine.open_read_only(self.ctx)
        state = reader.index_state(max_files=1)
        self.assertEqual(state["state"], "unknown")
        self.assertEqual(state["checked_files"], 1)


if __name__ == "__main__":
    unittest.main()
