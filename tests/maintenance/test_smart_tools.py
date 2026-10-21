"""Tests for the maintenance tools (Smart Merge, Architect Scanner, Vault Linter, templates).

Covers:
1. Smart Note Merge (smart_merge.py): Metadata union, redirect callout, wikilink rewriting.
2. Codebase Architect Scanner (architect_scan.py): Architecture extraction, module discovery, markdown/json output.
3. Vault Linter (vault_linter.py): En/Em-dash filename rule and freshness claim linting.
4. Note Template & Rules: Bi-temporal timeline schema and future agent preamble.
"""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
from respectedbrain.maintenance import vault_linter
from respectedbrain.maintenance import architect_scan
from respectedbrain.maintenance import smart_merge
from tests.support.files import make_context
from respectedbrain.core.resources import ResourceCatalog


class TestSmartMerge(unittest.TestCase):
    """Smart Note Merge tests."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.vault = Path(self.temp_dir.name)
        (self.vault / "500-Knowledge").mkdir(parents=True)
        (self.vault / "300-Projects").mkdir(parents=True)

        self.source = self.vault / "500-Knowledge" / "Eski_Not.md"
        self.source.write_text(
            "---\ntitle: Eski Not\ncreated: 2026-01-01\nmodified: 2026-01-10\ntags: [python, backend]\naliases: [Eski Alias]\n---\n# Eski Not İçeriği\nDetaylı açıklama burada.\n",
            encoding="utf-8",
        )

        self.target = self.vault / "500-Knowledge" / "Yeni_Not.md"
        self.target.write_text(
            "---\ntitle: Yeni Not\ncreated: 2026-02-01\nmodified: 2026-02-15\ntags: [fast-api]\n---\n# Yeni Not Başlığı\nAna içerik burada.\n",
            encoding="utf-8",
        )

        self.referrer = self.vault / "300-Projects" / "Proje.md"
        self.referrer.write_text(
            "# Proje\nReferans: [[Eski_Not]] ve [[Başka_Not]]\n",
            encoding="utf-8",
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_smart_merge_rejects_self_merge_without_data_loss(self):
        original_content = self.source.read_text(encoding="utf-8")
        with self.assertRaises(ValueError) as ctx:
            smart_merge.smart_merge(self.source, self.source, vault_root=self.vault)
        self.assertIn("kendisiyle birleştirilemez", str(ctx.exception))
        # Ensure zero data loss - content is 100% intact
        self.assertEqual(self.source.read_text(encoding="utf-8"), original_content)

    def test_smart_merge_merges_metadata_and_preserves_source_as_redirect(self):
        smart_merge.smart_merge(self.source, self.target, vault_root=self.vault)

        # 1. Source file still exists (never deleted)
        self.assertTrue(self.source.is_file())
        source_content = self.source.read_text(encoding="utf-8")
        self.assertIn("redirect: [[Yeni_Not]]", source_content)
        self.assertIn("type: redirect", source_content)
        self.assertIn("retired_at:", source_content)
        self.assertIn("[[Yeni_Not]]", source_content)

        # 2. Target file contains union of tags and aliases
        target_content = self.target.read_text(encoding="utf-8")
        self.assertIn("python", target_content)
        self.assertIn("backend", target_content)
        self.assertIn("fast-api", target_content)
        self.assertIn("Eski Not", target_content)
        self.assertIn("Birleştirilen Not: [[Eski_Not]]", target_content)
        self.assertIn("Detaylı açıklama burada.", target_content)

        # 3. Referrer note has wikilink rewritten from [[Eski_Not]] to [[Yeni_Not]]
        referrer_content = self.referrer.read_text(encoding="utf-8")
        self.assertIn("[[Yeni_Not]]", referrer_content)
        self.assertNotIn("[[Eski_Not]]", referrer_content)

    def test_smart_merge_preserves_scalar_tags_and_aliases(self):
        """Scalar (single-string) tags and aliases in frontmatter must not be dropped during merge."""
        source = self.vault / "500-Knowledge" / "Scalar_Source.md"
        source.write_text(
            "---\ntitle: Scalar Source\ntags: single-tag\naliases: single-alias\n---\n# Content\n",
            encoding="utf-8",
        )
        target = self.vault / "500-Knowledge" / "Scalar_Target.md"
        target.write_text(
            "---\ntitle: Scalar Target\ntags: [existing-tag]\naliases: [existing-alias]\n---\n# Content\n",
            encoding="utf-8",
        )

        smart_merge.smart_merge(source, target, self.vault)
        target_content = target.read_text(encoding="utf-8")
        self.assertIn("single-tag", target_content)
        self.assertIn("existing-tag", target_content)
        self.assertIn("single-alias", target_content)
        self.assertIn("existing-alias", target_content)

    def test_smart_merge_rejects_non_existent_source(self):
        non_existent = self.vault / "500-Knowledge" / "NonExistent.md"
        with self.assertRaises((FileNotFoundError, ValueError)):
            smart_merge.smart_merge(non_existent, self.target, vault_root=self.vault)


class TestArchitectScan(unittest.TestCase):
    """Codebase Architect Scanner tests."""

    def test_scan_codebase_detects_structure_and_modules(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            proj = Path(temp_dir)
            (proj / "src" / "api").mkdir(parents=True)
            (proj / "src" / "models").mkdir(parents=True)
            (proj / "package.json").write_text('{"name": "test-app", "dependencies": {"next": "14.0.0"}}', encoding="utf-8")
            (proj / "src" / "api" / "routes.ts").write_text("export const handle = () => {};", encoding="utf-8")
            (proj / "src" / "models" / "user.ts").write_text("export interface User { id: string; }", encoding="utf-8")

            report = architect_scan.scan_codebase(proj)
            self.assertEqual(report["name"], proj.name)
            self.assertTrue(any("next" in d for d in report["dependencies"]))
            self.assertGreater(len(report["modules"]), 0)

            md = architect_scan.to_markdown(report)
            self.assertIn("## For future agent", md)
            self.assertIn("## 1. Diller ve Dağılım", md)
            self.assertIn("## 2. Modül Hiyerarşisi", md)

    def test_scan_codebase_handles_missing_or_corrupt_manifest(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            proj = Path(temp_dir)
            (proj / "main.py").write_text("print('hello')", encoding="utf-8")
            # Missing package.json should not raise an exception
            report = architect_scan.scan_codebase(proj)
            self.assertEqual(report["name"], proj.name)
            self.assertEqual(report["dependencies"], [])

            # Corrupt package.json should not crash scan
            (proj / "package.json").write_text("{invalid json", encoding="utf-8")
            report_corrupt = architect_scan.scan_codebase(proj)
            self.assertEqual(report_corrupt["name"], proj.name)


class TestVaultLinter(unittest.TestCase):
    """Vault Linter En/Em-dash and Freshness claim linting tests."""

    def test_dash_checker_detects_and_fixes_en_em_dashes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir)
            bad_file = vault / "Not\u2013Tire.md"  # En-dash
            bad_file.write_text("# Not", encoding="utf-8")

            report = vault_linter.lint_vault(vault)
            self.assertEqual(report["filename_issues_count"], 1)
            self.assertIn("uzun tire", report["filename_issues"][0]["issue"])

            # Test fix option
            fixed = vault_linter.fix_dashes(vault)
            self.assertEqual(fixed, 1)
            self.assertTrue((vault / "Not-Tire.md").is_file())
            self.assertFalse(bad_file.exists())

    def test_freshness_claim_detection(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            vault = Path(temp_dir)
            (vault / "500-Knowledge").mkdir(parents=True)
            unverified = vault / "500-Knowledge" / "Pipeline.md"
            unverified.write_text(
                "# Pipeline\nŞu an pipeline sayısı: 12\n",
                encoding="utf-8",
            )
            verified = vault / "500-Knowledge" / "Pipeline_Dated.md"
            verified.write_text(
                "# Pipeline\nŞu an pipeline sayısı: 12 (as of 2026-09-01)\n",
                encoding="utf-8",
            )

            report = vault_linter.lint_vault(vault)
            self.assertEqual(report["freshness_warnings_count"], 1)
            self.assertIn("500-Knowledge/Pipeline.md:2", report["freshness_warnings"][0]["file"])


class TestTemplatesAndRules(unittest.TestCase):
    """Timeline schema and future agent preamble in templates & companion rules."""

    def test_note_template_contains_timeline_and_preamble(self):
        note_template = ResourceCatalog().read_text("vault-template/📋 Templates/Note.md")
        self.assertIn("timeline:", note_template)
        self.assertIn("from:", note_template)
        self.assertIn("until:", note_template)
        self.assertIn("learned:", note_template)
        self.assertIn("## For future agent", note_template)

    def test_kurallar_contains_smart_tool_directives(self):
        kurallar = ResourceCatalog().read_text("vault-template/🔮 850-Companion/Kurallar.md")
        self.assertIn("timeline:", kurallar)
        self.assertIn("## For future agent", kurallar)
        self.assertIn("(as of YYYY-MM-DD)", kurallar)


if __name__ == "__main__":
    unittest.main(verbosity=2)
