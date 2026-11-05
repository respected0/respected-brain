import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from respected_brain.memory import lifecycle
from respected_brain.memory.savings import savings_report


class ContextUsageTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.state = Path(temporary.name)
        self.now = datetime(2026, 10, 22, 12, 0, tzinfo=timezone.utc)

    def test_report_sums_recent_sessions_and_ignores_old_and_broken_lines(self):
        lifecycle.record_context_usage(self.state, "a" * 20, 4000, self.now - timedelta(days=1))
        lifecycle.record_context_usage(self.state, "b" * 20, 8000, self.now)
        lifecycle.record_context_usage(self.state, "c" * 20, 99999, self.now - timedelta(days=90))
        with (self.state / lifecycle.USAGE_FILE).open("a", encoding="utf-8") as handle:
            handle.write("not json\n")
        report = lifecycle.usage_report(self.state, self.now, 30)
        self.assertEqual((report["sessions"], report["context_chars_total"], report["context_chars_mean"], report["context_chars_max"]), (2, 12000, 6000, 8000))
        self.assertEqual((report["estimated_tokens_total"], report["estimated_tokens_per_session"]), (3000, 1500))

    def test_empty_history_reports_zeroes(self):
        report = lifecycle.usage_report(self.state, self.now)
        self.assertEqual((report["sessions"], report["context_chars_mean"], report["estimated_tokens_per_session"]), (0, 0, 0))

    def test_history_is_bounded(self):
        for index in range(2 * lifecycle.USAGE_KEEP + 2):
            lifecycle.record_context_usage(self.state, "s", index, self.now)
        lines = (self.state / lifecycle.USAGE_FILE).read_text(encoding="utf-8").splitlines()
        self.assertLessEqual(len(lines), lifecycle.USAGE_KEEP + 1)
        self.assertEqual(json.loads(lines[-1])["chars"], 2 * lifecycle.USAGE_KEEP + 1)

    def test_savings_report_keeps_usage_and_benchmark_separate(self):
        usage = lifecycle.usage_report(self.state, self.now)
        report = savings_report(usage)
        self.assertEqual(report["usage"], usage)
        benchmark = report["benchmark"]
        self.assertEqual((benchmark["full_tokens"], benchmark["compact_tokens"]), (1103.458, 47.452))
        self.assertTrue(benchmark["same_accuracy"])
        self.assertEqual(benchmark["reduction_percent"], 95.7)
        self.assertEqual(benchmark["low_budget_pass_rate"], 0.8)

    def test_benchmark_matches_the_checked_in_br012_report(self):
        import json
        from pathlib import Path
        report = json.loads((Path(__file__).resolve().parents[2] / "docs/evidence/br012-progressive.json").read_text(encoding="utf-8"))
        views = report["views"]
        from respected_brain.memory.savings import BENCHMARK
        self.assertEqual(views["full"]["tokens"], BENCHMARK["full_tokens"])
        self.assertEqual(views["compact-600"]["tokens"], BENCHMARK["compact_tokens"])
        self.assertEqual(views["compact-600"]["pass_rate"], BENCHMARK["compact_pass_rate"])
        self.assertEqual(views["compact-60"]["pass_rate"], BENCHMARK["low_budget_pass_rate"])

    def test_start_context_records_what_it_sent(self):
        vault = self.state / "vault"
        vault.mkdir()
        context = lifecycle.start_context(vault, self.state / "s", "session-x", self.now)
        row = json.loads((self.state / "s" / lifecycle.USAGE_FILE).read_text(encoding="utf-8").splitlines()[-1])
        self.assertEqual(row["chars"], len(context))


if __name__ == "__main__":
    unittest.main()
