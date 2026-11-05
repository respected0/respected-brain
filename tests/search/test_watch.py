"""BR-032: MCP süreci içindeki dizin izleyicisi; ayrı süreç yok, yalnızca FTS tazelenir."""
from __future__ import annotations

import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from respected_brain.core.errors import BusyError
from respected_brain.integrations.mcp.server import RespectedMcpServer
from respected_brain.search.engine import SearchEngine
from respected_brain.search.watch import SearchIndexWatcher
from tests.support.files import make_context


class SearchIndexWatcherTest(unittest.TestCase):
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
        return [row["path"] for row in self.engine.search(query, freshness="off")]

    def test_edit_is_indexed_after_debounce_and_unchanged_index_is_not_rewritten(self) -> None:
        self.note.write_text("# Karar\nyeniPostgres metni\n", encoding="utf-8")
        watcher = SearchIndexWatcher(self.engine, debounce=0.25)
        self.assertFalse(watcher.scan_once(now=0.0))
        self.assertEqual(self._paths("yeniPostgres"), [])
        with patch.object(self.engine, "index_vault", wraps=self.engine.index_vault) as indexing:
            self.assertTrue(watcher.scan_once(now=0.3))
            self.assertFalse(watcher.scan_once(now=5.0))
            self.assertEqual(indexing.call_count, 1)
        self.assertEqual(self._paths("yeniPostgres"), ["knowledge/karar.md"])
        self.assertEqual(self._paths("eskiSQLite"), [])

    def test_busy_writer_is_retried_on_a_later_tick(self) -> None:
        self.note.write_text("# Karar\nyeniPostgres metni\n", encoding="utf-8")
        watcher = SearchIndexWatcher(self.engine)
        self.assertFalse(watcher.scan_once(now=0.0))
        with patch.object(self.engine, "index_vault", side_effect=BusyError("busy")):
            self.assertFalse(watcher.scan_once(now=1.0))
        self.assertTrue(watcher.scan_once(now=2.0))
        self.assertEqual(self._paths("yeniPostgres"), ["knowledge/karar.md"])

    def test_large_vault_unknown_state_is_throttled(self) -> None:
        watcher = SearchIndexWatcher(self.engine, large_vault_interval=30.0)
        with patch.object(self.engine, "index_state", return_value={"state": "unknown"}), \
                patch.object(self.engine, "index_vault", wraps=self.engine.index_vault) as indexing:
            self.assertTrue(watcher.scan_once(now=0.0))
            self.assertFalse(watcher.scan_once(now=1.0))
            self.assertTrue(watcher.scan_once(now=30.0))
            self.assertEqual(indexing.call_count, 2)

    def test_stop_joins_the_background_thread(self) -> None:
        watcher = SearchIndexWatcher(self.engine, interval=0.01)
        watcher.start()
        thread = watcher._thread
        self.assertIsNotNone(thread)
        watcher.stop()
        self.assertFalse(thread.is_alive())

    def test_stdio_hosts_and_stops_the_watcher(self) -> None:
        server = RespectedMcpServer(self.ctx)
        with patch.object(server.index_watcher, "start") as start, \
                patch.object(server.index_watcher, "stop") as stop, \
                patch("sys.stdin", io.StringIO("")):
            server.run_stdio()
        start.assert_called_once_with()
        stop.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
