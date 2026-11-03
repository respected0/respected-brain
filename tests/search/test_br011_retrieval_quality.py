"""BR-011 retrieval quality: deterministic ranking, trust/decision tie-breaks, chunking, dedupe and relevance."""
from __future__ import annotations

import os
from pathlib import Path
import sqlite3
import tempfile
import unittest

from respected_brain.search.engine import SearchEngine
from tests.support.files import make_context


class RetrievalQualityTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.vault = self.root / "vault"
        self.vault.mkdir()
        self.engine = SearchEngine(make_context(self.root, self.vault))

    def note(self, path: str, body: str, mtime: float) -> None:
        target = self.vault / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8")
        os.utime(target, (mtime, mtime))

    def paths(self, query: str) -> list[str]:
        self.engine.index_vault()
        return [hit["path"] for hit in self.engine.search(query)]

    def test_equal_bm25_prefers_newer_note(self) -> None:
        self.note("decisions/framework-old.md", "# Framework decision\n\nWe selected Express for the API.\n", 1_000)
        self.note("decisions/framework.md", "# Framework decision\n\nExpress is superseded; the API uses Fastify.\n", 2_000)
        self.assertEqual(self.paths("current API framework")[0], "decisions/framework.md")

    def test_approved_source_beats_newer_pending_copy(self) -> None:
        self.note("facts/approved.md",
                  "---\ntitle: \"Deployment\"\nreview_status: \"approved\"\norigin: \"user_approved\"\n---\n"
                  "# Deployment\n\nDeployment uses blue-green.\n", 1_000)
        self.note("facts/pending.md",
                  "---\ntitle: \"Deployment\"\nreview_status: \"pending\"\norigin: \"model_inference\"\n---\n"
                  "# Deployment\n\nDeployment uses blue-green.\n", 2_000)
        self.assertEqual(self.paths("deployment blue-green")[0], "facts/approved.md")

    def test_active_decision_beats_expired_decision_with_newer_mtime(self) -> None:
        self.note("decisions/active.md", "# Decision\n\nUse Fastify [key: framework] [supersedes: express]\n", 1_000)
        self.note("decisions/expired.md", "# Decision\n\nUse Express [key: framework] [valid_until: 2020-01-01]\n", 2_000)
        self.assertEqual(self.paths("framework decision")[0], "decisions/active.md")

    def test_legacy_path_does_not_beat_current_even_if_newer_mtime(self) -> None:
        self.note("decisions/framework-old.md", "# Framework decision\n\nWe selected Express for the API.\n", 3_000)
        self.note("decisions/framework.md", "# Framework decision\n\nExpress is superseded; the API uses Fastify.\n", 1_000)
        self.assertEqual(self.paths("current API framework")[0], "decisions/framework.md")

    def test_long_note_is_chunked_and_returns_one_hit(self) -> None:
        filler = "\n\n".join(f"Paragraph {index} contains unrelated operations text." for index in range(80))
        self.note("notes/long.md", f"# Runbook\n\n{filler}\n\nThe recovery password is marmalade.\n\n{filler}\n", 1_000)
        hits = self.engine.search("marmalade")
        self.assertEqual([hit["path"] for hit in hits], ["notes/long.md"])
        self.assertIn("marmalade", hits[0]["snippet"])

    def test_identical_copies_are_deduplicated(self) -> None:
        body = "# Deployment\n\nDeployment uses blue-green.\n"
        self.note("a/copy.md", body, 1_000)
        self.note("b/copy.md", body, 1_000)
        self.assertEqual(len(self.paths("deployment blue-green")), 1)

    def test_pre_trust_index_schema_is_rebuilt_readably(self) -> None:
        self.note("notes/legacy.md", "# Legacy\n\nThe legacy note is readable.\n", 1_000)
        db = self.engine.db_path
        db.parent.mkdir(parents=True, exist_ok=True)
        db.unlink(missing_ok=True)
        con = sqlite3.connect(db)
        try:
            con.execute("CREATE TABLE files_meta (rel_path TEXT PRIMARY KEY, mtime REAL NOT NULL, "
                        "sha256 TEXT NOT NULL, title TEXT NOT NULL, category TEXT NOT NULL)")
            con.execute("CREATE VIRTUAL TABLE vault_fts USING fts5(rel_path UNINDEXED, title, content, tags, category)")
            con.commit()
        finally:
            con.close()
        engine = SearchEngine(self.engine.ctx)
        engine.index_vault()
        hits = engine.search("legacy readable")
        self.assertEqual([hit["path"] for hit in hits], ["notes/legacy.md"])

    def test_partial_single_term_noise_is_filtered(self) -> None:
        self.note("notes/weak.md", "# Weak\n\nalpha only.\n", 1_000)
        self.note("notes/strong.md", "# Strong\n\nalpha beta related.\n", 1_000)
        paths = self.paths("alpha beta gamma delta epsilon")
        self.assertIn("notes/strong.md", paths)
        self.assertNotIn("notes/weak.md", paths)


if __name__ == "__main__":
    unittest.main()
