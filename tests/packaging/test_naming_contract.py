#!/usr/bin/env python3
"""Version and vault marker contract."""

from __future__ import annotations

from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]


class NamingContractTest(unittest.TestCase):
    def test_current_manifest_uses_package_version_and_schema3_uuid_marker(self):
        from importlib.metadata import version
        from tests.support.files import make_context
        from uuid import UUID
        import json
        from respected_brain import __version__
        self.assertEqual(__version__,version("respected-brain"))
        with tempfile.TemporaryDirectory() as temporary:
            ctx=make_context(Path(temporary))
            marker=json.loads((ctx.paths.vault_root / ".respected.json").read_text(encoding="utf-8"))
            self.assertEqual(marker["schema_version"],3)
            self.assertEqual(str(UUID(marker["vault_id"])),ctx.paths.vault_id)
            self.assertFalse((ctx.paths.vault_root / ".respectedbrain-version").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
