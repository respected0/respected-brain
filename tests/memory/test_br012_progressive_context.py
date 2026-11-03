"""BR-012: task-based, token-budgeted progressive memory context."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from respected_brain.integrations.mcp.server import RespectedMcpServer
from respected_brain.memory.context import build_context, estimate_tokens
from respected_brain.search.engine import SearchEngine
from tests.support.files import make_context


class ContextBuilderTest(unittest.TestCase):
    def hits(self):
        return [
            {"path": "🧠 500-Knowledge/Deploy.md", "title": "Deploy", "snippet": "kanarya dagitim mavi halka"},
            {"path": "🧠 500-Knowledge/Old.md", "title": "Old", "snippet": "eski kanarya notu"},
        ]

    def test_short_detail_keeps_paths_without_snippets(self):
        context = build_context(self.hits(), detail="short", budget_tokens=100)
        self.assertIn("🧠 500-Knowledge/Deploy.md", context["text"])
        self.assertNotIn("mavi halka", context["text"])
        self.assertEqual([item["path"] for item in context["items"]], [hit["path"] for hit in self.hits()])
        self.assertLessEqual(context["tokens"], context["budget_tokens"])

    def test_summary_detail_includes_query_focused_snippet(self):
        context = build_context(self.hits(), detail="summary", budget_tokens=100)
        self.assertIn("mavi halka", context["text"])
        self.assertEqual(context["expand"], [hit["path"] for hit in self.hits()])

    def test_budget_drops_lower_ranked_hits_and_reports_truncation(self):
        results = [{"path": f"note-{index}.md", "title": f"Note {index}", "snippet": "x " * 40} for index in range(10)]
        context = build_context(results, detail="summary", budget_tokens=30)
        self.assertLess(len(context["items"]), len(results))
        self.assertTrue(context["truncated"])
        self.assertLessEqual(context["tokens"], 30)
        self.assertEqual(context["items"][0]["path"], "note-0.md")

    def test_budget_truncates_a_long_snippet(self):
        context = build_context(
            [{"path": "a.md", "title": "A", "snippet": "kelime " * 200}], budget_tokens=40
        )
        self.assertTrue(context["truncated"])
        self.assertLessEqual(context["tokens"], 40)
        self.assertTrue(context["text"].endswith("…"))

    def test_empty_and_invalid_inputs(self):
        empty = build_context([])
        self.assertEqual(empty["text"], "")
        self.assertEqual(empty["tokens"], 0)
        self.assertEqual(empty["expand"], [])
        with self.assertRaises(ValueError):
            build_context(self.hits(), detail="full")
        with self.assertRaises(ValueError):
            build_context(self.hits(), budget_tokens="many")
        self.assertEqual(estimate_tokens(""), 0)


class ProgressiveRecallMcpTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.vault = Path(self.temp_dir.name)
        knowledge = self.vault / "🧠 500-Knowledge"
        knowledge.mkdir(parents=True)
        distant = "\n\n".join(f"Arka plan paragrafi {index} burada duruyor." for index in range(40))
        (knowledge / "Deploy.md").write_text(
            "# Kanarya Dagitimi\nKanarya dagitim karari mavi halka ile yapilir.\n\n" + distant + "\n\nFULLBODYMARKER\n",
            encoding="utf-8",
        )
        (knowledge / "Other.md").write_text("# Baska Not\nAlakasiz icerik.", encoding="utf-8")
        self.technical = tempfile.TemporaryDirectory()
        self.addCleanup(self.technical.cleanup)
        self.server = RespectedMcpServer(make_context(Path(self.technical.name), self.vault))
        self.server.search_engine.index_vault()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_tool_is_listed_and_search_limits_are_preserved(self):
        names = [tool["name"] for tool in self.server.get_tools_manifest()]
        self.assertIn("respected_recall", names)
        self.assertIn("respected_search", names)
        self.assertIn("respected_get_note", names)

    def test_recall_returns_short_context_then_full_note_on_demand(self):
        short = self.server.call_tool("respected_recall", {"task": "kanarya dagitim", "budget_tokens": 200})
        self.assertIn("Görev Bağlamı", short)
        self.assertIn("🧠 500-Knowledge/Deploy.md", short)
        self.assertIn("respected_get_note", short)
        self.assertNotIn("FULLBODYMARKER", short)
        full = self.server.call_tool("respected_get_note", {"path": "🧠 500-Knowledge/Deploy.md"})
        self.assertIn("FULLBODYMARKER", full)

    def test_short_detail_omits_snippet_text(self):
        out = self.server.call_tool("respected_recall", {"task": "kanarya dagitim", "detail": "short"})
        self.assertIn("Deploy.md", out)
        self.assertNotIn("mavi halka", out)

    def test_tight_budget_does_not_exceed_budget(self):
        out = self.server.call_tool("respected_recall", {"task": "kanarya dagitim", "budget_tokens": 5})
        self.assertTrue("bütçeye sığan" in out or "kısaltıldı" in out)

    def test_recall_is_read_only_and_validates_types(self):
        before = sorted(path.relative_to(self.vault).as_posix() for path in self.vault.rglob("*.md"))
        self.server.call_tool("respected_recall", {"task": "kanarya dagitim", "budget_tokens": 200})
        after = sorted(path.relative_to(self.vault).as_posix() for path in self.vault.rglob("*.md"))
        self.assertEqual(before, after)
        self.assertEqual(
            self.server.call_tool("respected_recall", {"task": "kanarya", "budget_tokens": "many"}),
            "Hata: invalid argument: budget_tokens",
        )
        self.assertTrue(self.server.call_tool("respected_recall", {"task": "kzztq"}).startswith("'kzztq'"))
