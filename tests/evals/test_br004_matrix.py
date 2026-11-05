"""BR-004 integration matrix behavior: read-only, evidence-gated, client-specific detection."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tests.evals import br004_matrix


class MatrixTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="br004-matrix-")
        self.addCleanup(temporary.cleanup)
        self.home = Path(temporary.name).resolve()
        self.evidence = self.home / "evidence.json"

    def test_bare_gemini_folder_does_not_enable_antigravity(self):
        (self.home / ".gemini").mkdir()
        row = {item["id"]: item for item in br004_matrix.probe(self.home, self.evidence)["clients"]}
        self.assertFalse(row["antigravity"]["detected"])
        (self.home / ".gemini" / "antigravity-ide").mkdir()
        row = {item["id"]: item for item in br004_matrix.probe(self.home, self.evidence)["clients"]}
        self.assertTrue(row["antigravity"]["detected"])

    def test_probe_writes_nothing_and_evidence_free_clients_stay_limited(self):
        (self.home / ".claude").mkdir()
        before = sorted((str(path.relative_to(self.home)), path.read_bytes()) for path in self.home.rglob("*") if path.is_file())
        matrix = br004_matrix.probe(self.home, self.evidence)
        after = sorted((str(path.relative_to(self.home)), path.read_bytes()) for path in self.home.rglob("*") if path.is_file())
        self.assertEqual(before, after)
        self.assertTrue(matrix["writes_nothing"])
        self.assertTrue(all(item["support"] == "limited" for item in matrix["clients"]))
        self.assertFalse(self.evidence.exists())

    def test_real_test_evidence_alone_cannot_promote_an_uninstalled_client(self):
        self.evidence.write_text(json.dumps({
            "clients": {
                "claude": {"real_test_passed": True},
                "codex": {"real_test_passed": True},
            }
        }), encoding="utf-8")
        (self.home / ".claude").mkdir()
        (self.home / ".codex").mkdir()
        with patch.object(br004_matrix, "_executable", return_value=""):
            row = {item["id"]: item for item in br004_matrix.probe(self.home, self.evidence)["clients"]}
        self.assertFalse(row["claude"]["installed"])
        self.assertEqual(row["claude"]["support"], "limited")
        self.assertEqual(row["codex"]["support"], "limited")


if __name__ == "__main__":
    unittest.main()