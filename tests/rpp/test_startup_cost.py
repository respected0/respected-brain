"""Every Hub call starts the program once, so what an RPP manifest or health call imports is its cost (each avoided import is milliseconds per call)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROBE = """
import json, sys
from respected_brain.launcher import main
main(["rpp"])
print(json.dumps(sorted(sys.modules)), file=sys.stderr)
"""
# modules a manifest or health call has no use for
HEAVY = ("importlib.metadata", "respected_brain.cli", "respected_brain.vault.registry", "respected_brain.search", "respected_brain.rpp.memory",
         "respected_brain.rpp.memory_semantic", "respected_brain.rpp.integrations", "argparse")


class StartupCostTest(unittest.TestCase):
    def loaded(self, op):
        with tempfile.TemporaryDirectory() as temp:
            env = {**os.environ, "RESPECTED_DATA_DIR": str(Path(temp) / "data"), "RESPECTED_APP_DIR": str(Path(temp) / "app"),
                   "PYTHONPATH": str(ROOT / "src"), "PYTHONDONTWRITEBYTECODE": "1"}
            request = json.dumps({"rpp": "1", "op": op, "operation_id": None, "payload": {}})
            done = subprocess.run([sys.executable, "-c", PROBE], input=request, capture_output=True, text=True, env=env, cwd=temp, timeout=60)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertTrue(json.loads(done.stdout.splitlines()[0])["ok"], done.stdout)
        return set(json.loads(done.stderr.strip().splitlines()[-1]))

    def test_manifest_and_health_do_not_load_the_rest_of_the_program(self):
        for op in ("manifest", "health"):
            loaded = self.loaded(op)
            for name in HEAVY:
                self.assertNotIn(name, loaded, f"{op} imports {name}")

    def test_the_version_is_written_in_the_package_and_matches_pyproject(self):
        import re
        from packaging.version import Version
        import respected_brain
        declared = re.search(r'(?m)^version\s*=\s*"([^"]+)"', (ROOT / "pyproject.toml").read_text(encoding="utf-8")).group(1)
        self.assertEqual(respected_brain.__version__, str(Version(declared)))


if __name__ == "__main__":
    unittest.main()
