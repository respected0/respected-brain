"""BR-010: sorgu oncesi tazelik, eski metin sizdirmama, yeniden kurma ve eszamanli yazicilar."""
from __future__ import annotations

import os
from pathlib import Path
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor

from respected_brain.core.locking import exclusive_lock
from respected_brain.search.engine import SearchEngine
from tests.support.files import make_context


class IndexFreshnessTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.vault = self.root / "vault"
        (self.vault / "knowledge").mkdir(parents=True)
        self.note = self.vault / "knowledge" / "karar.md"
        self.note.write_text("# Karar\neskiSQLite metni\n", encoding="utf-8")
        self.ctx = make_context(self.root, self.vault)
        self.engine = SearchEngine(self.ctx)
        self.engine.index_vault()

    def _paths(self, query: str) -> list[str]:
        return [row["path"] for row in self.engine.search(query)]

    def test_external_edit_is_found_without_manual_reindex(self) -> None:
        self.note.write_text("# Karar\nyeniPostgres metni\n", encoding="utf-8")
        self.assertEqual(self._paths("yeniPostgres"), ["knowledge/karar.md"])
        self.assertEqual(self._paths("eskiSQLite"), [])

    def test_deleted_note_is_not_returned(self) -> None:
        self.note.unlink()
        self.assertEqual(self._paths("eskiSQLite"), [])

    def test_changed_content_with_preserved_mtime_never_returns_old_text(self) -> None:
        stamp = self.note.stat()
        self.note.write_text("# Karar\nyeniSQLite metni\n", encoding="utf-8")
        os.utime(self.note, ns=(stamp.st_atime_ns, stamp.st_mtime_ns))
        self.assertEqual(self.engine.index_state()["state"], "fresh")
        self.assertEqual(self._paths("eskiSQLite"), [])
        self.assertEqual(self._paths("yeniSQLite"), ["knowledge/karar.md"])

    def test_read_only_reader_filters_unindexed_changes(self) -> None:
        self.note.write_text("# Karar\nyeniPostgres metni\n", encoding="utf-8")
        reader = SearchEngine.open_read_only(self.ctx)
        self.assertEqual(reader.search("eskiSQLite"), [])

    def test_index_rebuilds_from_notes(self) -> None:
        self.engine._discard_cache()
        rebuilt = SearchEngine(self.ctx)
        self.assertEqual([row["path"] for row in rebuilt.search("eskiSQLite")], ["knowledge/karar.md"])

    def test_search_survives_busy_writer_and_never_returns_stale_text(self) -> None:
        self.note.write_text("# Karar\nyeniPostgres metni\n", encoding="utf-8")
        with exclusive_lock(self.ctx.paths.data_root / ".operation.lock"):
            self.assertEqual(self._paths("eskiSQLite"), [])
        self.assertEqual(self._paths("yeniPostgres"), ["knowledge/karar.md"])

    def test_concurrent_writers_and_queries_leave_a_current_index(self) -> None:
        def work(index: int) -> list[str]:
            if index % 2:
                SearchEngine(self.ctx).index_vault()
                return []
            return [row["path"] for row in self.engine.search("eskiSQLite")]

        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(work, range(4)))
        self.assertTrue(all(result in ([], ["knowledge/karar.md"]) for result in results))

        self.note.write_text("# Karar\nyeniPostgres metni\n", encoding="utf-8")
        self.assertEqual(self._paths("yeniPostgres"), ["knowledge/karar.md"])

    def test_invalid_freshness_and_off_mode(self) -> None:
        with self.assertRaises(ValueError):
            self.engine.search("karar", freshness="sometimes")
        self.assertEqual(self._paths("eskiSQLite"), ["knowledge/karar.md"])
        self.assertEqual(self.engine.search("eskiSQLite", freshness="off")[0]["path"], "knowledge/karar.md")


if __name__ == "__main__":
    unittest.main()
