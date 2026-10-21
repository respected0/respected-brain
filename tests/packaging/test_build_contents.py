"""What the frozen build and the installable package must contain (provenance module, clean UTF-8 sources)."""
from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

from tests.support.builder import build_dist

REPO_ROOT = Path(__file__).resolve().parents[2]


class FrozenPackagingTest(unittest.TestCase):
    def test_a_stale_installed_package_stops_the_build_before_freezing(self) -> None:
        # the frozen exe would carry the installed metadata's version, not the checkout's (seen once: 0.0.1 for 0.1.0)
        with mock.patch.object(build_dist, "version", return_value="0.0.1"), mock.patch("subprocess.run") as run:
            with self.assertRaisesRegex(RuntimeError, "not this checkout"):
                build_dist.build(platform="windows" if sys.platform == "win32" else "linux", output=Path(tempfile.gettempdir()))
        run.assert_not_called()


class EncodingRegressionTest(unittest.TestCase):
    """User-facing Turkish text must stay valid UTF-8 with no mojibake."""

    MOJIBAKE = set("\u00c3\u00c4\u00c5\u00c2\u00e2\u20ac\u0161\u0178\u02c6\u2039\u203a")

    def _assert_clean(self, relative: str) -> str:
        path = REPO_ROOT / relative
        text = path.read_bytes().decode("utf-8")
        suspicious = sorted({character for character in text if character in self.MOJIBAKE})
        self.assertEqual(suspicious, [], f"{relative} contains mojibake characters")
        controls = sorted({character for character in text if 0x80 <= ord(character) <= 0x9f})
        self.assertEqual(controls, [], f"{relative} contains C1 control characters from bad decoding")
        return text

    def test_cli_source_is_clean_utf8(self):
        self._assert_clean("src/respectedbrain/cli.py")


class PackagingIncludesProvenanceTest(unittest.TestCase):
    """The provenance verifier must ship in the package and the frozen build."""

    def test_provenance_module_is_part_of_installation_package(self):
        import respectedbrain.installation.provenance as module
        module_path = Path(module.__file__).resolve()
        self.assertEqual(module_path.name, "provenance.py")
        self.assertEqual(module_path.parent.name, "installation")
        self.assertEqual(module_path.parent.parent.name, "respectedbrain")

    def test_frozen_build_collects_all_respectedbrain_submodules(self):
        build_source = (REPO_ROOT / "packaging/build_dist.py").read_text(encoding="utf-8")
        self.assertIn('--collect-submodules', build_source)
        self.assertIn('respectedbrain', build_source)

    def test_setuptools_discovers_the_installation_package(self):
        pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn("[tool.setuptools.packages.find]", pyproject)
        self.assertIn('where = ["src"]', pyproject)


if __name__ == "__main__":
    unittest.main()
