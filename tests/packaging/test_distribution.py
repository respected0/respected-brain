"""Native artifacts must exist and run without checkout/Python on PATH."""
from pathlib import Path
import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


class FoundationDistributionTest(unittest.TestCase):
    def frozen(self):
        from respectedbrain.installation.payload import validate_package
        platform = "windows" if os.name == "nt" else "macos" if sys.platform == "darwin" else "linux"
        distribution = ROOT / "dist" / ("RespectedBrain.app" if platform == "macos" else "RespectedBrain")
        if not distribution.exists() and not os.environ.get("CI"):
            self.skipTest("no frozen build in dist/ (python packaging/build_dist.py); CI builds it and requires this test")
        document = validate_package(distribution, require_provenance=False)
        self.assertEqual(document["platform"], platform)
        return distribution, document

    def launcher(self, distribution, document, temporary, *args, stdin=None):
        env = {**os.environ, "PATH": str(Path(os.environ["SystemRoot"]) / "System32") if os.name == "nt" else "/usr/bin:/bin", "RESPECTED_APP_DIR": str(distribution), "RESPECTED_DATA_DIR": str(Path(temporary) / "data"), "PYTHONPATH": ""}
        result = subprocess.run([str(distribution / document["launcher"]), *map(str, args)], cwd=temporary, env=env, input=stdin, capture_output=True, text=True, encoding="utf-8", timeout=45)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        return result.stdout

    def test_frozen_runs_without_checkout_or_python(self):
        distribution, document = self.frozen()
        with tempfile.TemporaryDirectory(prefix="Türkçe 🧠 ") as temporary:
            self.assertEqual(self.launcher(distribution, document, temporary, "--version").strip(), document["version"])
            self.assertFalse((Path(temporary) / "data").exists())
        self.assertFalse((distribution / "runtime").exists())
        resources = [name for name in document["files"] if name.endswith("respectedbrain/resources/defaults.json")]
        self.assertEqual(len(resources), 1)

    def test_frozen_serves_vault_maps_search_hook_and_mcp(self):
        distribution, document = self.frozen()
        with tempfile.TemporaryDirectory(prefix="Respected Türkçe 🧠 ") as temporary:
            run = lambda *args, stdin=None: self.launcher(distribution, document, temporary, *args, stdin=stdin)
            vault = Path(temporary) / "Kasa 🧠"
            vault.mkdir()
            (vault / "keep.md").write_text("# Notum\n", encoding="utf-8")
            identity = run("vault", "register", vault).strip()
            self.assertIn(identity, json.loads(run("vault", "list")))
            run("maps", "--vault-id", identity)
            run("search", "--vault-id", identity, "--json", "Notum")
            run("hook", "--vault-id", identity, "--provider", "claude", "--event", "precompact", stdin="{}")
            reply = run("mcp", "--vault-id", identity, stdin='{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}\n')
            self.assertEqual(json.loads(reply)["id"], 1)
            self.assertEqual((vault / "keep.md").read_text(encoding="utf-8"), "# Notum\n")

    def test_distribution_tampering_fails_before_launcher(self):
        from respectedbrain.installation.payload import validate_package
        from respectedbrain.core.errors import OwnershipConflict
        from tests.support.packages import seed_package
        with tempfile.TemporaryDirectory() as temporary:
            package = seed_package(Path(temporary))
            (package / "respectedbrain.exe").write_bytes(b"changed")
            with self.assertRaises(OwnershipConflict):
                validate_package(package, require_provenance=False)
