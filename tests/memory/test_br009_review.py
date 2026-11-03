#!/usr/bin/env python3
"""Tests for BR-009 inbox review and promotion."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

from tests.support.files import make_context
from respected_brain.memory import inbox, review
from respected_brain.memory.provenance import parse_frontmatter
from respected_brain.rpp import server as rpp


class ReviewTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)
        self.vault = self.root / "vault"
        self.ctx = make_context(self.root / "tech", self.vault)

    def create(self, operation_id: str, title: str, body: str, source: str = "mcp") -> str:
        result = inbox.create_note(lambda: self.ctx, self.ctx.paths.data_root, operation_id, grant_id="mcp",
                                   source=source, inbox_rel=inbox.MCP_INBOX, title=title, body=body, tags=[])
        return result["path"]

    def content(self, relative: str) -> str:
        return (self.vault / relative).read_text(encoding="utf-8")

    def ledger(self):
        path = self.ctx.paths.data_root / "memory-review" / "ledger.jsonl"
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]

    def test_accept_promotes_to_knowledge_and_is_traceable(self) -> None:
        path = self.create("mcp-review-0001", "Kural", "Sunucu her zaman UTC kullanır.")
        self.assertEqual(review.queue(self.vault, self.ctx.paths.data_root)["items"][0]["path"], path)

        result = review.apply(self.ctx, path, "accept")

        self.assertTrue(result["promoted_to"].startswith("🧠 500-Knowledge/Reviewed/"))
        fields, _ = parse_frontmatter(self.content(path))
        self.assertEqual(fields["review_status"], "approved")
        self.assertEqual(fields["origin"], "user_approved")
        self.assertEqual(fields["promoted_to"], result["promoted_to"])
        permanent = self.content(result["promoted_to"])
        self.assertIn("Sunucu her zaman UTC kullanır.", permanent)
        self.assertIn("promoted_from", permanent)
        self.assertEqual(review.queue(self.vault, self.ctx.paths.data_root)["items"], [])
        entry = self.ledger()[-1]
        self.assertEqual(entry["action"], "accept")
        self.assertNotEqual(entry["before_sha256"], entry["after_sha256"])

    def test_reject_blocks_identical_reproposal_and_flags_repeat(self) -> None:
        path = self.create("mcp-review-0002", "Yanlış kural", "Bu kural hatalı.")
        review.apply(self.ctx, path, "reject", reason="olgu hatası")

        self.assertFalse((self.vault / "🧠 500-Knowledge" / "Reviewed").exists())
        self.assertEqual(parse_frontmatter(self.content(path))[0]["review_status"], "rejected")
        with self.assertRaisesRegex(inbox.MemoryOpError, "already rejected"):
            self.create("mcp-gamma-0003", "Yanlış kural", "Bu kural hatalı.")

        second = self.create("mcp-delta-0004", "Yanlış kural", "Düzeltilmiş ama hâlâ incelemede.")
        fields = parse_frontmatter(self.content(second))[0]
        self.assertEqual(fields["review_reason"], "repeated-rejection")
        self.assertEqual(fields["learning_candidate"], "true")
        review.apply(self.ctx, second, "reject")
        self.assertTrue(self.ledger()[-1]["learning_candidate"])

    def test_correct_promotes_corrected_body(self) -> None:
        path = self.create("mcp-review-0005", "Sürüm", "Sürüm 1.0 kullanılıyor.")
        result = review.apply(self.ctx, path, "correct", corrected_body="Sürüm 2.0 kullanılıyor.",
                              corrected_title="Sürüm kuralı")

        self.assertIn("Sürüm 2.0 kullanılıyor.", self.content(result["promoted_to"]))
        self.assertNotIn("Sürüm 1.0 kullanılıyor.", self.content(result["promoted_to"]))
        self.assertIn("Sürüm kuralı", self.content(result["promoted_to"]))
        entry = self.ledger()[-1]
        self.assertEqual(entry["action"], "correct")
        self.assertNotEqual(entry["before_sha256"], entry["after_sha256"])

    def test_defer_hides_until_requested_and_remains_pending(self) -> None:
        path = self.create("mcp-review-0006", "Ertelenen", "Sonra bakılacak.")
        review.apply(self.ctx, path, "defer", until="2026-12-01")

        self.assertEqual(review.queue(self.vault, self.ctx.paths.data_root)["items"], [])
        shown = review.queue(self.vault, self.ctx.paths.data_root, include_deferred=True)["items"]
        self.assertEqual(shown[0]["path"], path)
        fields = parse_frontmatter(self.content(path))[0]
        self.assertEqual(fields["review_status"], "pending")
        self.assertEqual(fields["review"], "deferred")
        self.assertEqual(review.apply(self.ctx, path, "accept")["review_status"], "approved")

    def test_model_cannot_review_its_own_note(self) -> None:
        path = self.create("mcp-review-0007", "Model kaydı", "Model kendi kaydını onaylayamaz.")
        with self.assertRaisesRegex(inbox.MemoryOpError, "cannot review"):
            review.apply(self.ctx, path, "accept", reviewer="model")
        self.assertEqual(parse_frontmatter(self.content(path))[0]["review_status"], "pending")

    def test_rpp_review_ops_are_registered(self) -> None:
        path = self.create("mcp-review-0008", "RPP kuralı", "RPP üzerinden onaylanır.")
        with patch.dict(os.environ, {"RESPECTED_APP_DIR": str(self.root / "app"),
                                     "RESPECTED_DATA_DIR": str(self.ctx.paths.data_root)}):
            found = rpp.serve(json.dumps({"rpp": "1", "op": "memory.review.queue", "payload": {}}),
                              data_root=str(self.ctx.paths.data_root))
            self.assertTrue(found["ok"], found)
            self.assertEqual(found["result"]["items"][0]["path"], path)
            applied = rpp.serve(json.dumps({"rpp": "1", "op": "memory.review.apply", "operation_id": "review-op-0001",
                                            "payload": {"path": path, "action": "accept"}}),
                                data_root=str(self.ctx.paths.data_root))
        self.assertTrue(applied["ok"], applied)
        self.assertTrue(applied["result"]["promoted_to"])


if __name__ == "__main__":
    unittest.main()