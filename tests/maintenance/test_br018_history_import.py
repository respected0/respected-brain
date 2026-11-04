"""BR-018: gecmis oturum onizleme, secim, maskeleme, tarih ve arsiv sinirlari."""
from __future__ import annotations

import contextlib
import datetime as dt
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from respected_brain.maintenance.ingestion.mine_agent_history import AgentHistoryMiner, main
from tests.support.files import make_context

SECRET = "sk-proj-abcdefghijklmnopqrstuvwxyz123456"


class HistoryImportTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.vault = self.root / "vault"
        (self.vault / "daily").mkdir(parents=True)
        self.home = self.root / "home"
        self.ctx = make_context(self.root, self.vault)
        self.transcript = (
            self.home / ".gemini" / "antigravity-ide" / "brain" / "conversation-one"
            / ".system_generated" / "logs" / "transcript.jsonl"
        )
        self.transcript.parent.mkdir(parents=True)
        records = [
            {
                "type": "USER_INPUT",
                "created_at": "2021-03-04T05:06:07Z",
                "content": f"<USER_REQUEST>api_key = {SECRET} eski karari acikla</USER_REQUEST>",
            },
            {
                "type": "PLANNER_RESPONSE",
                "created_at": "2021-03-04T05:07:08Z",
                "content": "Eski mimari SQLite FTS5 kullaniyordu ve bu karar korunmali.",
            },
        ]
        self.transcript.write_text(
            "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records),
            encoding="utf-8",
        )
        self.session = {
            "agent": "antigravity",
            "id": "antigravity_conversation-one",
            "path": self.transcript,
            "mtime": dt.datetime.now(),
        }
        self.miner = AgentHistoryMiner(
            self.vault,
            state_file=self.ctx.paths.state_dir / "imported_sessions.json",
            temp_dir=self.ctx.paths.cache_dir,
        )

    def test_preview_is_read_only_masked_and_shows_source_date(self) -> None:
        before = sorted(self.vault.rglob("*"))
        preview = self.miner.preview_session(self.session)

        self.assertIsNotNone(preview)
        self.assertEqual(preview["id"], "antigravity_conversation-one")
        self.assertEqual(preview["date"], "2021-03-04 05:06:07")
        self.assertEqual(preview["turns"], 1)
        self.assertIn("transcript.jsonl", preview["source"])
        self.assertNotIn(SECRET, preview["summary"])
        self.assertIn("REDACTED:secret", preview["summary"])
        self.assertFalse(preview["already_imported"])
        self.assertEqual(sorted(self.vault.rglob("*")), before)

    def test_apply_requires_explicit_session_and_preserves_event_date(self) -> None:
        with patch.object(Path, "home", return_value=self.home):
            preview_out = io.StringIO()
            with contextlib.redirect_stdout(preview_out):
                self.assertEqual(main(["--source", "antigravity"], ctx=self.ctx), 0)
            self.assertEqual(list((self.vault / "daily").glob("*.md")), [])
            self.assertNotIn(SECRET, preview_out.getvalue())
            self.assertIn("REDACTED:secret", preview_out.getvalue())

            refused = io.StringIO()
            with contextlib.redirect_stdout(refused):
                self.assertEqual(main(["--source", "antigravity", "--apply"], ctx=self.ctx), 2)
            self.assertEqual(list((self.vault / "daily").glob("*.md")), [])

            applied = io.StringIO()
            with contextlib.redirect_stdout(applied):
                code = main(
                    ["--source", "antigravity", "--apply", "--session-id", self.session["id"]],
                    ctx=self.ctx,
                )

        self.assertEqual(code, 0)
        notes = list((self.vault / "daily").glob("*.md"))
        self.assertEqual(len(notes), 1)
        self.assertEqual(dt.datetime.fromtimestamp(notes[0].stat().st_mtime, tz=dt.timezone.utc).strftime("%Y-%m-%d"), "2021-03-04")
        content = notes[0].read_text(encoding="utf-8")
        self.assertIn('valid_at: "2021-03-04"', content)
        self.assertIn('created: "2021-03-04 05:06:07"', content)
        self.assertIn(f'recorded_at: "{dt.datetime.now().strftime("%Y-%m-%d")}', content)
        self.assertIn("status: imported", content)
        self.assertIn("source_file:", content)
        self.assertIn("transcript.jsonl", content)
        self.assertIn("freshness: dated", content)
        self.assertIn("review_status: pending", content)
        self.assertNotIn(SECRET, content)

    def test_reimport_is_idempotent_and_user_edit_is_not_overwritten(self) -> None:
        parsed = self.miner.parse_session(self.session)
        self.assertIsNotNone(parsed)
        first = self.miner.import_session(parsed)
        second = self.miner.import_session(parsed)
        self.assertEqual(first, second)
        self.assertEqual(len(list((self.vault / "daily").glob("*.md"))), 1)

        edited = first.read_text(encoding="utf-8") + "\nKullanici notu\n"
        first.write_text(edited, encoding="utf-8")
        with self.assertRaises(ValueError):
            self.miner.import_session(parsed)
        self.assertEqual(first.read_text(encoding="utf-8"), edited)

    def test_archive_is_off_by_default_and_opt_in_redacted_outside_vault(self) -> None:
        parsed = self.miner.parse_session(self.session)
        source_before = self.transcript.read_bytes()
        self.miner.import_session(parsed)
        self.assertFalse((self.ctx.paths.data_root / "archives").exists())

        archive_dir = self.ctx.paths.data_root / "archives" / "agent-history"
        archiving = AgentHistoryMiner(
            self.vault,
            state_file=self.ctx.paths.state_dir / "archived_sessions.json",
            temp_dir=self.ctx.paths.cache_dir,
            archive_dir=archive_dir,
        )
        archived = archiving.archive_session(parsed)
        self.assertIsNotNone(archived)
        self.assertTrue(archived.is_relative_to(archive_dir))
        self.assertFalse(archived.is_relative_to(self.vault))
        archive_text = archived.read_text(encoding="utf-8")
        self.assertNotIn(SECRET, archive_text)
        self.assertIn("[REDACTED:secret]", archive_text)
        self.assertEqual(self.transcript.read_bytes(), source_before)
        if os.name != "nt":
            self.assertEqual(archived.stat().st_mode & 0o777, 0o600)

        with self.assertRaises(ValueError):
            AgentHistoryMiner(
                self.vault,
                state_file=self.ctx.paths.state_dir / "bad_archive.json",
                archive_dir=self.vault / "archive",
            )


if __name__ == "__main__":
    unittest.main()
