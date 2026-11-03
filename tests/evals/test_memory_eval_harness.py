"""Tests for the BR-001 memory evaluation harness."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests.evals import harness


def scenario(**overrides):
    base = {
        "id": "X01",
        "category": "recall",
        "notes": [{"path": "notes/x.md", "content": "# X\nFastify is current.\n"}],
        "query": "current framework",
        "expected_paths": ["notes/x.md"],
        "answer_terms": ["Fastify"],
    }
    base.update(overrides)
    return base


def result(*items):
    return {"results": [{"path": path, "snippet": snippet} for path, snippet in items]}


class DatasetTest(unittest.TestCase):
    def test_dataset_has_required_size_and_categories(self):
        data = harness.load_dataset()
        scenarios = data["scenarios"]
        self.assertGreaterEqual(len(scenarios), 40)
        self.assertLessEqual(len(scenarios), 50)
        self.assertEqual({s["category"] for s in scenarios}, set(harness.CATEGORIES))
        self.assertEqual(len({s["id"] for s in scenarios}), len(scenarios))

    def test_missing_category_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "bad.json"
            path.write_text('{"version":"1","scenarios":[]}', encoding="utf-8")
            with self.assertRaises(ValueError):
                harness.load_dataset(path)


class ScoringTest(unittest.TestCase):
    def test_correct_source_and_answer_pass(self):
        score = harness.score_result(scenario(), result(("notes/x.md", "uses Fastify")), 5)
        self.assertTrue(score["pass"])
        self.assertTrue(score["hit1"])
        self.assertTrue(score["answer"])

    def test_wrong_source_fails(self):
        score = harness.score_result(scenario(), result(("notes/y.md", "Fastify is mentioned")), 5)
        self.assertFalse(score["pass"])
        self.assertFalse(score["hit5"])

    def test_missing_answer_term_fails(self):
        score = harness.score_result(scenario(), result(("notes/x.md", "something else")), 5)
        self.assertFalse(score["answer"])
        self.assertFalse(score["pass"])

    def test_stale_note_above_current_fails(self):
        case = scenario(expected_paths=["notes/new.md"], stale_paths=["notes/old.md"], expect_top1=True,
                        answer_terms=["Fastify"])
        score = harness.score_result(
            case, result(("notes/old.md", "Express"), ("notes/new.md", "Fastify")), 5)
        self.assertEqual(score["stale_above_current"], 1)
        self.assertFalse(score["pass"])

    def test_unknown_query_needs_zero_hits(self):
        case = scenario(no_answer=True, expected_paths=[], answer_terms=[])
        self.assertTrue(harness.score_result(case, result(), 5)["pass"])
        self.assertFalse(harness.score_result(case, result(("notes/x.md", "noise")), 5)["pass"])


class EndToEndTest(unittest.TestCase):
    def test_one_real_fixture_is_indexed_and_retrieved(self):
        case = harness.load_dataset()["scenarios"][0]
        with tempfile.TemporaryDirectory(prefix="brain-eval-test-") as temporary:
            data, vault_id, _, fixture = harness._build_fixture(Path(temporary).resolve(), case)
            self.assertGreaterEqual(fixture["index"]["indexed"], 1)
            raw, info, latency = harness._run_query(case, "fts", data, vault_id, 5, 400)
            score = harness.score_result(case, raw, 5)
            self.assertEqual(info["mode"], "fts")
            self.assertGreaterEqual(latency, 0)
            self.assertTrue(score["pass"], raw)

    def test_markdown_report_contains_dataset_and_modes(self):
        report = {
            "generated_at": "now", "brain_version": "test",
            "dataset": {"scenario_count": 50, "sha256": "abc"},
            "settings": {"modes": ["fts"], "repeats": 1, "limit": 5, "snippet_chars": 400},
            "prompt": "p", "model": {"semantic": None},
            "modes": {"fts": {"aggregate": {
                "pass_rate": 1.0, "hit1": 1.0, "hit5": 1.0, "mrr": 1.0, "answer_accuracy": 1.0,
                "source_coverage": 1.0, "stale_above_current": 0, "no_answer_accuracy": 1.0,
                "latency_ms": {"p50": 1, "p95": 2}, "context_tokens_estimate": 10.0,
                "repeat_pass_rate": [1.0], "repeat_stdev": 0.0,
                "categories": {category: {"scenarios": 1, "pass_rate": 1.0} for category in harness.CATEGORIES},
            }, "scenarios": {}}},
        }
        text = harness.render_markdown(report)
        self.assertIn("BR-001", text)
        self.assertIn("abc", text)
        self.assertIn("`fts`", text)


if __name__ == "__main__":
    unittest.main()