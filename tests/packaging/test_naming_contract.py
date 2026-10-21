#!/usr/bin/env python3
"""The old product name never reaches a current surface; version and public guide contracts."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
FORBIDDEN_BRAND_FRAGMENTS = ("Respot Brain", "RESPOT", "Respot", "respot")


def find_forbidden_occurrences(
    root: Path,
    tracked_paths: tuple[Path, ...],
    allowlist: set[Path],
) -> list[tuple[Path, int, str]]:
    occurrences: list[tuple[Path, int, str]] = []
    for relative in tracked_paths:
        if relative in allowlist:
            continue
        try:
            lines = (root / relative).read_text(encoding="utf-8").splitlines()
        except (FileNotFoundError, UnicodeDecodeError):
            continue
        for line_number, line in enumerate(lines, start=1):
            for fragment in FORBIDDEN_BRAND_FRAGMENTS:
                if fragment in line:
                    occurrences.append((relative, line_number, fragment))
                    break
    return occurrences


class NamingContractTest(unittest.TestCase):
    def test_repository_current_surfaces_have_no_unallowlisted_legacy_brand(self):
        result = subprocess.run(
            ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
            cwd=ROOT,
            capture_output=True,
            check=True,
        )
        paths = tuple(
            Path(line)
            for line in result.stdout.decode("utf-8", errors="replace").split("\0")
            if line
            and not Path(line).is_relative_to("qa-evidence")
            and not Path(line).is_relative_to("qa-workspaces")
        )
        allowlist = {Path("tests/packaging/test_naming_contract.py")}

        occurrences = find_forbidden_occurrences(ROOT, paths, allowlist)

        self.assertEqual(occurrences, [])

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

        for fragment in FORBIDDEN_BRAND_FRAGMENTS:
            for name, content in guides.items():
                self.assertNotIn(fragment, content, f"{name}: legacy current-facing name")

    def test_scanner_reports_legacy_brand_only_outside_the_allowlist(self):
        scanner = globals().get("find_forbidden_occurrences")
        self.assertIsNotNone(scanner, "naming-contract scanner is missing")
        with tempfile.TemporaryDirectory(prefix="respected-names-") as temporary:
            root = Path(temporary)
            (root / "current.txt").write_text("Respected Brain\n", encoding="utf-8")
            (root / "legacy.txt").write_text(
                "Respot Brain\nRESPOT-GLOBAL\nrespot-brain\n.respot-backups\n",
                encoding="utf-8",
            )
            (root / "historical.md").write_text("Respot Brain\n", encoding="utf-8")

            occurrences = scanner(
                root,
                (Path("current.txt"), Path("legacy.txt"), Path("historical.md")),
                {Path("historical.md")},
            )

        self.assertEqual(
            occurrences,
            [
                (Path("legacy.txt"), 1, "Respot Brain"),
                (Path("legacy.txt"), 2, "RESPOT"),
                (Path("legacy.txt"), 3, "respot"),
                (Path("legacy.txt"), 4, "respot"),
            ],
        )

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
