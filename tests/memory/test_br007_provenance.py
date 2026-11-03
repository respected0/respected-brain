"""BR-007: provenance metadata stays additive, verifiable and review-aware."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import tempfile
import unittest
from pathlib import Path

from respected_brain.core.context import ModelResult
from respected_brain.memory import compile as compiler
from respected_brain.memory import flush
from respected_brain.memory import inbox
from respected_brain.memory import provenance
from tests.support.files import make_context

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "memory-provenance"
SUMMARY = "## Bağlam\nKalıcı bağlam.\n\n## Alınan Kararlar\n- Karar."


def comment_document(text: str) -> dict:
    match = re.search(r"<!-- RESPECTED-PROVENANCE: (\{.*?\}) -->", text)
    if match is None:
        raise AssertionError("provenance comment missing")
    return json.loads(match.group(1))


class ProvenanceMetadataTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="br007-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.ctx = make_context(self.root)

    def test_legacy_fixture_reads_as_unknown_without_changing_bytes(self) -> None:
        path = FIXTURES / "v0-legacy.md"
        original = path.read_bytes()
        metadata = provenance.read_provenance(path.read_text(encoding="utf-8"))
        self.assertTrue(metadata["legacy"])
        self.assertEqual(metadata["provenance_version"], 0)
        self.assertEqual(metadata["review_status"], "unreviewed")
        self.assertEqual(metadata["origin"], "unknown")
        self.assertEqual(metadata["source_agent"], "unknown")
        self.assertEqual(path.read_bytes(), original)

    def test_migration_adds_metadata_and_preserves_body(self) -> None:
        original = (FIXTURES / "v0-legacy.md").read_text(encoding="utf-8")
        migrated = provenance.migrate_text(original, source_agent="migration")
        metadata = provenance.read_provenance(migrated)
        self.assertFalse(metadata["legacy"])
        self.assertEqual(metadata["provenance_version"], 1)
        self.assertEqual(metadata["recorded_at"], "2025-01-02 09:00:00")
        self.assertEqual(metadata["review_status"], "unreviewed")
        self.assertIn("# Eski karar\n\nGövde aynen korunmalı.", migrated)
        self.assertEqual(original, (FIXTURES / "v0-legacy.md").read_text(encoding="utf-8"))

    def test_versioned_fixtures_distinguish_model_and_approved_origins(self) -> None:
        model_metadata = provenance.read_provenance((FIXTURES / "v1-model-inference.md").read_text(encoding="utf-8"))
        approved_metadata = provenance.read_provenance((FIXTURES / "v1-user-approved.md").read_text(encoding="utf-8"))
        self.assertEqual(model_metadata["origin"], "model_inference")
        self.assertEqual(model_metadata["review_status"], "pending")
        self.assertEqual(approved_metadata["origin"], "user_approved")
        self.assertEqual(approved_metadata["review_status"], "approved")

    def test_model_metadata_cannot_self_approve(self) -> None:
        content = "---\ntitle: \"Model\"\nreview_status: \"approved\"\norigin: \"user_approved\"\n---\n# Model\n"
        fields = provenance.build_provenance(source_agent="compiler", origin="model_inference", review_status="approved")
        enriched = provenance.enrich_frontmatter(content, fields)
        metadata = provenance.read_provenance(enriched)
        self.assertEqual(metadata["origin"], "model_inference")
        self.assertEqual(metadata["review_status"], "pending")
        self.assertEqual(enriched.count("review_status:"), 1)
        self.assertEqual(enriched.count("origin:"), 1)

    def test_daily_session_records_source_session_and_summary_hash(self) -> None:
        state = self.ctx.paths.state_dir
        state.mkdir(parents=True, exist_ok=True)
        daily = self.ctx.paths.vault_root / "daily"
        daily.mkdir(parents=True, exist_ok=True)
        now = dt.datetime(2026, 11, 3, 12, 0)
        flush._upsert_daily_session(self.ctx.paths.vault_root, state, SUMMARY, "turn", now, "session-7", "codex")
        text = (daily / "2026-11-03.md").read_text(encoding="utf-8")
        document = comment_document(text)
        self.assertEqual(document["source_agent"], "codex")
        self.assertEqual(document["session_id"], "session-7")
        self.assertEqual(document["record_type"], "session_summary")
        self.assertEqual(document["origin"], "model_inference")
        self.assertEqual(document["review_status"], "pending")
        self.assertEqual(document["source_ref"], "session://codex/session-7")
        self.assertEqual(document["source_sha256"], hashlib.sha256(SUMMARY.encode("utf-8")).hexdigest())
        self.assertEqual(provenance.session_ids_in_text(text), ["session-7"])

    def test_inbox_capture_distinguishes_mcp_model_output_from_user_capture(self) -> None:
        result = inbox.create_note(lambda: self.ctx, self.ctx.paths.data_root, "mcp-operation-12345678",
                                   grant_id="mcp", source="mcp", inbox_rel="Inbox", title="MCP notu",
                                   body="Model önerisi.", tags=[], extra_front=["type: lesson", "review: pending"])
        text = (self.ctx.paths.vault_root / result["path"]).read_text(encoding="utf-8")
        metadata = provenance.read_provenance(text)
        self.assertEqual(metadata["origin"], "model_inference")
        self.assertEqual(metadata["record_type"], "lesson")
        self.assertEqual(metadata["review_status"], "pending")
        self.assertEqual(metadata["source_agent"], "mcp")
        self.assertEqual(metadata["source_sha256"], hashlib.sha256("Model önerisi.\n".encode("utf-8")).hexdigest())
        self.assertIn("review: pending", text)

    def test_partial_or_absent_metadata_reads_as_safe_defaults(self) -> None:
        partial = provenance.read_provenance("---\nprovenance_version: 1\nsource_agent: \"codex\"\n---\n# Kısmi\n")
        self.assertFalse(partial["legacy"])
        self.assertEqual(partial["source_agent"], "codex")
        self.assertEqual(partial["record_type"], "note")
        self.assertEqual(partial["review_status"], "unreviewed")
        self.assertEqual(partial["origin"], "unknown")
        self.assertEqual(partial["source_sha256"], "")
        bare = provenance.read_provenance("# Başlıksız\n")
        self.assertTrue(bare["legacy"])
        self.assertEqual(bare["review_status"], "unreviewed")
        self.assertEqual(bare["origin"], "unknown")

    def test_extra_front_cannot_claim_provenance_and_orchestrator_writes_stay_pending(self) -> None:
        forged = inbox.create_note(lambda: self.ctx, self.ctx.paths.data_root, "mcp-operation-87654321",
                                   grant_id="mcp", source="mcp", inbox_rel="Inbox", title="Sahte",
                                   body="Model çıktısı.", tags=[],
                                   extra_front=["origin: user_approved", "review_status: approved", "source_sha256: fake"])
        text = (self.ctx.paths.vault_root / forged["path"]).read_text(encoding="utf-8")
        metadata = provenance.read_provenance(text)
        self.assertEqual(metadata["origin"], "model_inference")
        self.assertEqual(metadata["review_status"], "pending")
        self.assertNotEqual(metadata["source_sha256"], "fake")
        self.assertEqual(text.count("origin:"), 1)
        self.assertEqual(text.count("review_status:"), 1)
        orchestrated = inbox.create_note(lambda: self.ctx, self.ctx.paths.data_root, "orchestrator-op-12345678",
                                         grant_id="grant", source="orchestrator", inbox_rel="Inbox", title="Öneri",
                                         body="Agent önerisi.", tags=[])
        orchestrated_text = (self.ctx.paths.vault_root / orchestrated["path"]).read_text(encoding="utf-8")
        orchestrated_metadata = provenance.read_provenance(orchestrated_text)
        self.assertEqual(orchestrated_metadata["origin"], "model_inference")
        self.assertEqual(orchestrated_metadata["review_status"], "pending")
        self.assertEqual(orchestrated_metadata["source_agent"], "orchestrator")

    def test_compile_marks_model_concepts_pending_and_references_daily_hash(self) -> None:
        vault = self.ctx.paths.vault_root
        (vault / "knowledge").mkdir(parents=True, exist_ok=True)
        (vault / "knowledge/index.md").write_text("# Index\n", encoding="utf-8")
        (vault / "knowledge/log.md").write_text("# Log\n", encoding="utf-8")
        daily = vault / "daily"
        daily.mkdir(parents=True, exist_ok=True)
        daily_file = daily / "2026-11-02.md"
        daily_file.write_text("# Daily\nKarar.\n", encoding="utf-8")
        digest = hashlib.sha256(daily_file.read_bytes()).hexdigest()

        class Model:
            def run(self, prompt, *, cwd, mode, timeout):
                concept = cwd / "knowledge/concepts/karar.md"
                concept.parent.mkdir(parents=True, exist_ok=True)
                concept.write_text("---\ntitle: \"Karar\"\nreview_status: \"approved\"\norigin: \"user_approved\"\n---\n# Karar\n\nGövde.\n", encoding="utf-8")
                (cwd / "knowledge/index.md").write_text("# Index\n\nKarar.\n", encoding="utf-8")
                return ModelResult("", "codex", None)

        self.assertEqual(compiler.compile_memory(self.ctx, model=Model(), now=dt.datetime(2026, 11, 3, 9, 0)), 0)
        text = (vault / "knowledge/concepts/karar.md").read_text(encoding="utf-8")
        metadata = provenance.read_provenance(text)
        self.assertEqual(metadata["origin"], "model_inference")
        self.assertEqual(metadata["review_status"], "pending")
        self.assertEqual(metadata["source_agent"], "compiler")
        self.assertEqual(metadata["record_type"], "knowledge_concept")
        self.assertEqual(metadata["source_ref"], "daily/2026-11-02.md")
        self.assertEqual(metadata["source_sha256"], digest)
        self.assertIn("# Karar\n\nGövde.", text)


if __name__ == "__main__":
    unittest.main()
