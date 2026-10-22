"""Automatic index freshness: detached refresh launch is throttled; refresh_now is incremental."""

from __future__ import annotations

import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from uuid import uuid4

from respected_brain.core.config import ConfigStore
from respected_brain.rpp.integrations import _context
from respected_brain.search import freshness


class FreshnessTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="idx-fresh-")
        self.addCleanup(temporary.cleanup)
        base = Path(temporary.name).resolve()
        self.data, self.vault = base / "data", base / "vault"
        self.data.mkdir()
        self.vault.mkdir()
        (self.vault / "a.md").write_text("# A\nalpha text\n", encoding="utf-8")
        patcher = patch.dict(os.environ, {"RESPECTED_APP_DIR": str(base / "app"), "RESPECTED_DATA_DIR": str(self.data)})
        patcher.start()
        self.addCleanup(patcher.stop)

        def mutate(document):
            vault_id = str(uuid4())
            document["vaults"][vault_id] = {"path": str(self.vault)}
            document["active_vault_id"] = vault_id
        ConfigStore(self.data).update(mutate)
        _, self.ctx = _context(self.data, {})

    def test_refresh_now_is_incremental(self):
        first = freshness.refresh_now(self.ctx)
        self.assertTrue(first["refreshed"])
        self.assertEqual(first["indexed"], 1)
        again = freshness.refresh_now(self.ctx)
        self.assertEqual((again["indexed"], again["skipped"]), (0, 1))

    def test_refresh_while_another_writer_is_admitted_reports_busy_instead_of_failing(self):
        # Two AI sessions ending together: the second flush's best-effort refresh met the first one's admission lock
        # and raised BusyError, so a flush whose summary was already saved exited 1.
        from respected_brain.core.locking import exclusive_lock
        with exclusive_lock(self.ctx.paths.data_root / ".operation.lock"):
            result = freshness.refresh_now(self.ctx, attempts=2, wait=0.01)
        self.assertEqual(result, {"refreshed": False, "reason": "busy"})
        self.assertTrue(freshness.refresh_now(self.ctx)["refreshed"])


if __name__ == "__main__":
    unittest.main()


class CaptureModeTest(unittest.TestCase):
    setUp = FreshnessTest.setUp
    """capture_mode = manual: hooks must not summarise sessions on their own, the user triggers capture."""

    def launch(self, mode, payload=None):
        import dataclasses
        from unittest.mock import MagicMock
        from respected_brain.memory import lifecycle
        ctx = dataclasses.replace(self.ctx, config={**self.ctx.config, "preferences": {"capture_mode": mode}})
        with patch.object(lifecycle.subprocess, "Popen", return_value=MagicMock()) as popen:
            lifecycle._launch_flush(ctx, "claude", payload=payload or {"session_id": "s1"}, reason="sessionend", maybe_compile=True)
        return popen.call_args.args[0]

    def test_auto_flushes_and_manual_only_refreshes_the_index(self):
        self.assertIn("flush", self.launch("auto"))
        kept = set(self.ctx.paths.state_dir.glob("hookin-*"))
        manual = self.launch("manual", payload={"session_id": "s1", "transcript_path": str(self.data / "t.jsonl")})
        self.assertIn("index-refresh", manual)
        self.assertNotIn("flush", manual)
        self.assertEqual(set(self.ctx.paths.state_dir.glob("hookin-*")), kept)  # a manual session leaves no new hook payload
        pending = list(self.ctx.paths.state_dir.glob("pending-capture-*.json"))
        self.assertEqual(len(pending), 1)  # ...but the session is remembered so the user can capture it later

    def test_capture_run_needs_confirmation_and_runs_the_catch_up(self):
        from respected_brain.rpp import memory_capture as rpp_memory_capture
        self.assertRaises(Exception, rpp_memory_capture.run, self.data, {})
        with patch("respected_brain.memory.flush.catch_up_unflushed_sessions", return_value=2) as catch_up, \
                patch("respected_brain.memory.flush.compile_catch_up", return_value=0):
            result = rpp_memory_capture.run(self.data, {"confirm": True})
        self.assertEqual(result, {"captured_sessions": 2, "compile_status": 0, "pending_left": 0})
        self.assertTrue(catch_up.called)


class OpenCommandTest(unittest.TestCase):
    """`open` opens the vault folder; no local server exists any more."""

    def test_open_opens_the_vault_folder_and_nothing_else(self):
        import io
        from contextlib import redirect_stdout
        from unittest.mock import patch
        from respected_brain import cli
        for name in ("open",):
            with patch.object(cli.os, "startfile", create=True) as startfile, patch.object(cli.subprocess, "Popen") as popen, \
                    patch.object(cli, "bootstrap") as boot, redirect_stdout(io.StringIO()) as out:
                boot.return_value.paths.vault_root = Path("C:/vault-x") if os.name == "nt" else Path("/vault-x")
                self.assertEqual(cli.main([name, "--vault-id", "00000000-0000-0000-0000-000000000000"]), 0)
            self.assertEqual(startfile.call_count + popen.call_count, 1, name)
            self.assertIn("vault-x", out.getvalue())
