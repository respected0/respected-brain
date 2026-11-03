"""Structured, redacted memory diagnostics."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest

from respected_brain.memory.diagnostics import reason_for, record_health, safe_reason


class DiagnosticsTest(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory(prefix="brain-health-")
        self.addCleanup(temporary.cleanup)
        self.state = Path(temporary.name) / "state"
        self.state.mkdir()
        self.health = self.state / "health.json"

    def load(self) -> dict:
        return json.loads(self.health.read_text(encoding="utf-8"))

    def test_records_structured_correlated_fields(self) -> None:
        record_health(
            self.state,
            stage="summarize",
            reason="summary-empty",
            component="flush",
            operation_id="op-0001",
            session_id="session-0001",
            provider="codex",
            event="end",
            now=datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc),
        )
        payload = self.load()
        self.assertEqual(payload["status"], "degraded")
        self.assertEqual(payload["error"], "summary-empty")
        self.assertEqual(payload["reason"], "summary-empty")
        self.assertEqual(payload["component"], "flush")
        self.assertEqual(payload["stage"], "summarize")
        self.assertEqual(payload["operation_id"], "op-0001")
        self.assertEqual(payload["session_id"], "session-0001")
        self.assertEqual(payload["provider"], "codex")
        self.assertEqual(payload["event"], "end")
        self.assertEqual(payload["ts"], 1767323045)
        self.assertEqual(payload["updated_at"], "2026-01-02T03:04:05+00:00")

    def test_generates_operation_id_when_absent(self) -> None:
        record_health(self.state, stage="capture", reason="hook-metadata-invalid", component="hooks")
        operation_id = self.load()["operation_id"]
        self.assertEqual(len(operation_id), 32)
        int(operation_id, 16)

    def test_free_form_exception_text_never_enters_health(self) -> None:
        secret = "/home/user/private/transcript.jsonl sk-live-12345"
        self.assertEqual(safe_reason(secret), "unclassified")
        self.assertEqual(reason_for(ValueError(secret)), "error:ValueError")

        record_health(self.state, stage="capture", reason=secret, component="hooks")
        record_health(self.state, stage="capture", reason=ValueError(secret), component="hooks")
        raw = self.health.read_text(encoding="utf-8")
        self.assertNotIn("private", raw)
        self.assertNotIn("sk-live", raw)
        self.assertEqual(self.load()["error"], "unclassified")

    def test_corrupt_or_nan_health_is_replaced_safely(self) -> None:
        self.health.write_text('{"unknown": NaN, "status": "degraded"}', encoding="utf-8")
        record_health(self.state, stage="daily_write", reason="daily-append-failed", component="flush")
        payload = self.load()
        self.assertEqual(payload["error"], "daily-append-failed")
        self.assertEqual(payload["status"], "degraded")
        self.assertNotIn("unknown", payload)

    def test_warning_keeps_status_and_does_not_duplicate(self) -> None:
        self.health.write_text('{"status": "ok"}', encoding="utf-8")
        record_health(self.state, stage="compile", reason="warn:directive-shaped-input",
                      component="compile", warning=True)
        record_health(self.state, stage="compile", reason="warn:directive-shaped-input",
                      component="compile", warning=True)
        payload = self.load()
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["warnings"], ["warn:directive-shaped-input"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
