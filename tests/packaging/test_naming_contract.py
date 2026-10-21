#!/usr/bin/env python3
"""Version and public guide contracts."""

from __future__ import annotations

from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]


class NamingContractTest(unittest.TestCase):
    def test_current_public_guides_use_the_modular_native_contract(self):
        guides = {
            name: (ROOT / "docs/guides" / name if name != "README.md" else ROOT / name).read_text(encoding="utf-8")
            for name in ("README.md", "SETUP.md", "SETUP-WINDOWS.md", "MULTI_AI.md", "UPDATE.md")
        }
        combined = "\n".join(guides.values())

        for provider in ("Claude", "Codex", "Cursor", "Antigravity"):
            self.assertIn(provider, combined)
        for profile in ("windows-wsl", "windows-native"):
            self.assertIn(profile, combined)
        self.assertIn("Respected Brain", guides["README.md"])
        self.assertIn("https://github.com/respected0/respected-secondbrain", guides["README.md"])
        for current in ("respectedbrain", "--vault-id", "DataRoot", "AppRoot"):
            self.assertIn(current, combined)
        for retired in ("scripts/update_respected.py", ".respected/schedule-backups", ".respected/update-backups"):
            self.assertNotIn(retired, combined)
        self.assertIn("MIT", guides["README.md"])

    def test_current_manifest_uses_package_version_and_schema3_uuid_marker(self):
        from importlib.metadata import version
        from tests.support.files import make_context
        from uuid import UUID
        import json
        from respectedbrain import __version__
        self.assertEqual(__version__,version("respectedbrain"))
        with tempfile.TemporaryDirectory() as temporary:
            ctx=make_context(Path(temporary))
            marker=json.loads((ctx.paths.vault_root / ".respected.json").read_text(encoding="utf-8"))
            self.assertEqual(marker["schema_version"],3)
            self.assertEqual(str(UUID(marker["vault_id"])),ctx.paths.vault_id)
            self.assertFalse((ctx.paths.vault_root / ".respectedbrain-version").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
