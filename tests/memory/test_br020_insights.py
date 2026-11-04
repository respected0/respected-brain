"""BR-020: read-only skill suggestions, opt-in session search, handoff context, and vault health."""

from __future__ import annotations

import datetime as dt
import json
import os
from pathlib import Path
import tempfile
import unittest

from respected_brain.integrations.mcp.server import RespectedMcpServer
from respected_brain.memory import events, insights
from tests.support.files import make_context, run_cli, snapshot


NOW = dt.datetime(2026, 11, 4, 9, 0, tzinfo=dt.timezone.utc)


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class InsightTestBase(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.ctx = make_context(self.root)
        self.vault = self.ctx.paths.vault_root
        self.data = self.ctx.paths.data_root

    def tearDown(self) -> None:
        self.temporary.cleanup()


class SkillSuggestionTest(InsightTestBase):
    def test_suggestions_use_ledger_and_events_without_writing(self) -> None:
        ledger = self.data / "memory-review" / "ledger.jsonl"
        write(ledger, json.dumps({"action": "reject", "title_key": "obsidian tema css",
                                  "learning_candidate": True}, ensure_ascii=False) + "\n")
        events.record_event(self.vault, "codex", "session_end", "s1",
                            learnings=["kod review gate"], now=NOW)
        before = (snapshot(self.vault), snapshot(self.data))

        result = insights.skill_suggestions(self.data, self.vault, limit=10)

        self.assertGreaterEqual(result["count"], 2)
        by_title = {item["title"]: item for item in result["suggestions"]}
        self.assertEqual(by_title["obsidian tema css"]["matching_skill"], "obsidian-layout")
        self.assertEqual(by_title["obsidian tema css"]["action"], "use-existing-skill")
        self.assertEqual(by_title["kod review gate"]["matching_skill"], "yazilim-kalite")
        self.assertEqual(before, (snapshot(self.vault), snapshot(self.data)))

    def test_limit_is_bounded(self) -> None:
        ledger = self.data / "memory-review" / "ledger.jsonl"
        lines = [json.dumps({"action": "reject", "title_key": f"aday {index}", "learning_candidate": True})
                 for index in range(30)]
        write(ledger, "\n".join(lines) + "\n")
        result = insights.skill_suggestions(self.data, limit=5)
        self.assertEqual(result["count"], 30)
        self.assertEqual(len(result["suggestions"]), 5)
        self.assertTrue(result["truncated"])


class SessionSearchTest(InsightTestBase):
    def test_searches_only_the_redacted_archive_and_masks_secrets(self) -> None:
        archive = self.data / "archives" / "agent-history"
        write(archive / "codex_abcd.jsonl",
              '{"text":"deploy sk-abcdefghijklmnopqrstuvwxyz012345"}\n'
              '{"text":"other deploy note"}\n')
        write(self.data / "archives" / "outside.jsonl", '{"text":"deploy outside"}\n')

        result = insights.session_search(self.data, "deploy", limit=5)

        self.assertEqual(result["count"], 2)
        snippets = " ".join(item["snippet"] for item in result["results"])
        self.assertIn("[REDACTED:provider-token]", snippets)
        self.assertNotIn("sk-abcdefghijklmnopqrstuvwxyz012345", snippets)
        self.assertNotIn("outside", snippets)
        self.assertEqual({item["agent"] for item in result["results"]}, {"codex"})

    def test_rejects_short_queries_and_empty_limits(self) -> None:
        with self.assertRaises(ValueError):
            insights.session_search(self.data, "x")
        write(self.data / "archives" / "agent-history" / "codex_a.jsonl", '{"text":"deploy"}\n')
        result = insights.session_search(self.data, "deploy", limit=0)
        self.assertEqual(result["results"], [])


class HandoffContextTest(InsightTestBase):
    def test_provider_filter_and_budget(self) -> None:
        codex_event = events.record_event(self.vault, "codex", "session_end", "s1", context="codex deploy context",
                            decisions=["Postgres kullan [key: database]"], now=NOW)
        later = NOW + dt.timedelta(minutes=1)
        events.record_event(self.vault, "claude", "session_end", "s2", context="claude test context",
                            decisions=["SQLite kullan [key: database]"], todos=["release notes"],
                            threads=[{"title": "deploy", "status": "active", "summary": "mavi halka"}], now=later)

        result = insights.handoff_context(self.vault, budget_tokens=600)
        self.assertEqual(result["providers"], ["claude", "codex"])
        self.assertIn("claude test context", result["text"])
        self.assertIn("Postgres kullan", result["text"])
        self.assertIn("SQLite kullan", result["text"])
        self.assertIn("release notes", result["text"])

        filtered = insights.handoff_context(self.vault, provider="codex", budget_tokens=600)
        self.assertEqual(filtered["providers"], ["codex"])
        self.assertNotIn("claude test context", filtered["text"])
        self.assertEqual(filtered["latest_event_id"], codex_event["id"])

        bounded = insights.handoff_context(self.vault, budget_tokens=20)
        self.assertLessEqual(bounded["tokens"], 20)

    def test_empty_vault_returns_bounded_empty_context(self) -> None:
        result = insights.handoff_context(self.vault, budget_tokens=100)
        self.assertEqual(result["text"], "")
        self.assertEqual(result["providers"], [])
        self.assertEqual(result["budget_tokens"], 100)


class HealthReportTest(InsightTestBase):
    def test_reports_duplicates_conflicts_and_lint_without_writing(self) -> None:
        body = " ".join(f"kelime{index} ortak icerik" for index in range(20))
        write(self.vault / "duplicate-a.md", "# A\n\n" + body + "\n")
        write(self.vault / "duplicate-b.md", "# B\n\n" + body + "\n")
        write(self.vault / "dead.md", "# Dead\n\n[[Missing Note]]\n")
        events.record_event(self.vault, "codex", "session_end", "s1",
                            decisions=["Postgres kullan [key: database]"], now=NOW)
        events.record_event(self.vault, "claude", "session_end", "s2",
                            decisions=["SQLite kullan [key: database]"], now=NOW + dt.timedelta(minutes=1))
        before = (snapshot(self.vault), snapshot(self.data))

        result = insights.health_report(self.vault, limit=5)

        self.assertFalse(result["healthy"])
        self.assertGreaterEqual(result["duplicates"]["count"], 1)
        self.assertEqual(result["conflicts"]["count"], 2)
        self.assertGreaterEqual(result["lint"]["dead_links_count"], 1)
        self.assertLessEqual(len(result["duplicates"]["top"]), 5)
        self.assertLessEqual(len(result["conflicts"]["top"]), 5)
        self.assertEqual(before, (snapshot(self.vault), snapshot(self.data)))


class SurfaceTest(InsightTestBase):
    def test_cli_and_mcp_expose_read_only_insights(self) -> None:
        server = RespectedMcpServer(self.ctx)
        self.assertIn("respected_insights", {tool["name"] for tool in server.get_tools_manifest()})
        payload = json.loads(server.call_tool("respected_insights", {"view": "handoff", "budget_tokens": 80}))
        self.assertIn("handoff", payload)
        self.assertLessEqual(payload["handoff"]["tokens"], 80)

        env = {**os.environ, "RESPECTED_APP_DIR": str(self.ctx.paths.app_root),
               "RESPECTED_DATA_DIR": str(self.data), "PYTHONUTF8": "1",
               "PYTHONPATH": os.pathsep.join(filter(None, (str(Path(__file__).resolve().parents[2] / "src"),
                                                            os.environ.get("PYTHONPATH"))))}
        completed = run_cli(["insights", "health", "--vault", str(self.vault), "--limit", "3"],
                            env=env, cwd=self.root)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("health", json.loads(completed.stdout))


if __name__ == "__main__":
    unittest.main()