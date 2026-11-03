"""Tests for the evaluation report comparator (BR-003)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tests.evals import compare

DATASET = "a" * 64


def report(**aggregate):
    base = {
        "pass_rate": 0.6,
        "hit1": 0.5,
        "hit5": 1.0,
        "mrr": 0.7,
        "answer_accuracy": 1.0,
        "source_coverage": 1.0,
        "no_answer_accuracy": 1.0,
        "stale_above_current": 0,
        "latency_ms": {"p50": 40.0, "p95": 50.0},
    }
    base.update(aggregate)
    return {
        "schema_version": "1",
        "brain_version": "0.1.0b1",
        "dataset": {"sha256": DATASET},
        "modes": {"fts": {"status": "ok", "aggregate": base}},
    }


class CompareTest(unittest.TestCase):
    def test_identical_reports_pass(self):
        result = compare.compare(report(), report())
        self.assertTrue(result["ok"])
        self.assertEqual(result["regressions"], [])

    def test_lower_pass_rate_is_a_regression(self):
        result = compare.compare(report(), report(pass_rate=0.5))
        self.assertFalse(result["ok"])
        self.assertIn("fts: pass_rate 0.6 -> 0.5", result["regressions"])

    def test_more_stale_leaks_are_a_regression(self):
        result = compare.compare(report(), report(stale_above_current=1))
        self.assertFalse(result["ok"])
        self.assertIn("fts: stale_above_current 0 -> 1", result["regressions"])

    def test_latency_beyond_tolerance_is_a_regression(self):
        result = compare.compare(report(), report(latency_ms={"p50": 40.0, "p95": 66.0}))
        self.assertFalse(result["ok"])
        self.assertTrue(any("latency_ms.p95" in item for item in result["regressions"]))

    def test_dataset_mismatch_is_rejected(self):
        changed = report()
        changed["dataset"] = {"sha256": "b" * 64}
        with self.assertRaises(ValueError):
            compare.compare(report(), changed)

    def test_cli_exit_code_and_json_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            base, new, out = root / "base.json", root / "new.json", root / "out.json"
            base.write_text(json.dumps(report()), encoding="utf-8")
            new.write_text(json.dumps(report(pass_rate=0.5)), encoding="utf-8")
            code = compare.main([str(base), str(new), "--json-out", str(out)])
            self.assertEqual(code, 1)
            self.assertFalse(json.loads(out.read_text(encoding="utf-8"))["ok"])


if __name__ == "__main__":
    unittest.main()