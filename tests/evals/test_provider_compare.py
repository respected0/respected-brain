"""Contracts for the provider quality comparison harness."""
from __future__ import annotations

import unittest

from tests.evals.provider_compare import compare, markdown


def report(label, provider, pass_rate, facts, truncated=0, sha="abc"):
    return {
        "schema_version": "1",
        "dataset": {"sha256": sha},
        "model": {"provider": provider, "label": label},
        "aggregate": {
            "pass_rate": pass_rate,
            "schema_valid_rate": 1.0,
            "fact_coverage": facts,
            "prompt_coverage": facts,
            "section_accuracy": pass_rate,
            "truncated_facts": truncated,
            "hallucination_scenarios": 0,
            "secret_leak_scenarios": 0,
            "injection_leak_scenarios": 0,
            "raw_transcript_stored": 0,
            "flush_failures": 0,
            "categories": {"decision": {"pass_rate": pass_rate, "fact_coverage": facts}},
        },
    }


class ProviderCompareTest(unittest.TestCase):
    def test_reports_deltas_and_regressions(self):
        base = report("claude/haiku", "claude", 0.8, 0.9)
        new = report("openrouter/model", "openrouter", 0.7, 0.9, truncated=2)
        result = compare(base, new)
        self.assertFalse(result["ok"])
        self.assertEqual(result["deltas"]["pass_rate"], -0.1)
        self.assertIn("pass_rate", result["regressions"][0])
        self.assertIn("truncated_facts", " ".join(result["regressions"]))
        self.assertIn("openrouter/model", markdown(result))

    def test_same_quality_is_ok(self):
        result = compare(report("a", "claude", 0.8, 0.9), report("b", "openrouter", 0.8, 0.9))
        self.assertTrue(result["ok"])
        self.assertEqual(result["regressions"], [])

    def test_different_datasets_are_refused(self):
        with self.assertRaises(ValueError):
            compare(report("a", "claude", 0.8, 0.9), report("b", "openrouter", 0.8, 0.9, sha="other"))


if __name__ == "__main__":
    unittest.main()
