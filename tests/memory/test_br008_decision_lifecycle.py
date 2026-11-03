#!/usr/bin/env python3
"""Tests for BR-008 decision lifecycle projection."""

from __future__ import annotations

import datetime as dt
import tempfile
from pathlib import Path
import unittest

from tests.support.files import make_context
from respected_brain.integrations.mcp.server import RespectedMcpServer
from respected_brain.memory import decisions, events


NOW = dt.datetime(2026, 11, 3, 12, 0, tzinfo=dt.timezone.utc)


def record(vault: Path, session: str, decision: str, when: dt.datetime, provider: str = "codex"):
    return events.record_event(vault, provider, "session_end", session, decisions=[decision], now=when)


class DecisionLifecycleTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)
        self.vault = self.root / "vault"
        (self.vault / "🔮 850-Companion").mkdir(parents=True)

    def collect(self):
        return decisions.collect(events.list_events(self.vault), now=NOW)

    def test_parse_separates_markers(self) -> None:
        parsed = decisions.parse_decision(
            "Fastify kullan [key: web-framework] [supersedes: express] [valid_until: 2026-12-01]"
        )
        self.assertEqual(parsed["text"], "Fastify kullan")
        self.assertEqual(parsed["subject"], "web-framework")
        self.assertEqual(parsed["supersedes"], ["express"])
        self.assertEqual(parsed["valid_until"], "2026-12-01")
        self.assertIsNone(decisions.parse_decision(""))

    def test_express_superseded_by_fastify(self) -> None:
        record(self.vault, "s1", "Express kullan [key: web-framework]", dt.datetime(2026, 10, 1, tzinfo=dt.timezone.utc))
        record(self.vault, "s2", "Fastify kullan [key: web-framework] [supersedes: web-framework]",
               dt.datetime(2026, 11, 1, tzinfo=dt.timezone.utc))
        records = self.collect()

        active = decisions.current(records)
        self.assertEqual([item["text"] for item in active], ["Fastify kullan"])
        old = next(item for item in decisions.history(records) if "Express" in item["text"])
        self.assertEqual(old["status"], "superseded")
        self.assertEqual(old["supersession_reason"], "explicit")
        self.assertTrue(old["superseded_by"])

    def test_conflicting_active_decisions_need_review(self) -> None:
        record(self.vault, "s1", "Postgres kullan [key: database]", dt.datetime(2026, 10, 1, tzinfo=dt.timezone.utc))
        record(self.vault, "s2", "SQLite kullan [key: database]", dt.datetime(2026, 11, 1, tzinfo=dt.timezone.utc))
        records = self.collect()

        self.assertEqual({item["status"] for item in records}, {"disputed"})
        self.assertTrue(all(item["review_reason"] == "conflicting-decisions" for item in records))
        self.assertEqual(len(decisions.review_items(records)), 2)

    def test_validity_expiry_marks_superseded(self) -> None:
        record(self.vault, "s1", "Geçici karar [key: temp] [valid_until: 2026-10-01]",
               dt.datetime(2026, 9, 1, tzinfo=dt.timezone.utc))
        item = self.collect()[0]
        self.assertEqual(item["status"], "superseded")
        self.assertEqual(item["supersession_reason"], "validity-expired")
        self.assertEqual(item["valid_until"], "2026-10-01")

    def test_unresolved_supersedes_goes_to_review(self) -> None:
        record(self.vault, "s1", "Yeni karar [key: x] [supersedes: olmayan-karar]",
               dt.datetime(2026, 10, 1, tzinfo=dt.timezone.utc))
        item = self.collect()[0]
        self.assertTrue(item["review_required"])
        self.assertEqual(item["review_reason"], "unresolved-supersedes")
        self.assertEqual(item["unresolved_supersedes"], ["olmayan-karar"])

    def test_projection_writes_current_and_history(self) -> None:
        record(self.vault, "s1", "Express kullan [key: web-framework]", dt.datetime(2026, 10, 1, tzinfo=dt.timezone.utc))
        record(self.vault, "s2", "Fastify kullan [key: web-framework] [supersedes: web-framework]",
               dt.datetime(2026, 11, 1, tzinfo=dt.timezone.utc))
        events.project_companion(self.vault)

        text = (self.vault / "🔮 850-Companion" / "Decisions.md").read_text(encoding="utf-8")
        self.assertIn("## Güncel", text)
        self.assertIn("Fastify kullan", text)
        self.assertIn("## Geçmiş / Yerine Geçilen", text)
        self.assertIn("Express kullan", text)
        self.assertIn("## İnsan İncelemesi Gerekli", text)

    def test_mcp_history_is_opt_in(self) -> None:
        record(self.vault, "s1", "Express kullan [key: web-framework]", dt.datetime(2026, 10, 1, tzinfo=dt.timezone.utc))
        record(self.vault, "s2", "Fastify kullan [key: web-framework] [supersedes: web-framework]",
               dt.datetime(2026, 11, 1, tzinfo=dt.timezone.utc))
        server = RespectedMcpServer(make_context(self.root / "tech", self.vault))

        current_only = server.call_tool("respected_get_decisions", {})
        self.assertIn("Fastify kullan", current_only)
        self.assertNotIn("Express kullan", current_only)

        with_history = server.call_tool("respected_get_decisions", {"include_history": True})
        self.assertIn("Express kullan", with_history)


if __name__ == "__main__":
    unittest.main()