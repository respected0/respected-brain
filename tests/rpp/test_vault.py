"""The install state the manifest reports, from the product's own install record (temporary roots only)."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from respected_brain.rpp import server as rpp


class InstallStateTest(unittest.TestCase):
    def test_changed_or_missing_owned_files_report_repair_needed_but_config_changes_do_not(self):
        import hashlib
        with tempfile.TemporaryDirectory(prefix="rpp-state-") as name:
            base = Path(name).resolve()
            data = base / "data"
            data.mkdir()
            app_file, config = base / "app.bin", base / "config.json"
            app_file.write_bytes(b"one")
            config.write_bytes(b"cfg")
            rows = [{"path": str(app_file), "sha256": hashlib.sha256(b"one").hexdigest(), "role": "application"},
                    {"path": str(config), "sha256": hashlib.sha256(b"cfg").hexdigest(), "role": "technical"}]
            (data / "install-manifest.json").write_text(json.dumps({"schema_version": 3, "files": rows, "external": []}), encoding="utf-8")
            state = lambda: rpp.serve(json.dumps({"rpp": "1", "op": "manifest", "payload": {}}), data_root=data)["result"]["install_state"]
            self.assertEqual(state(), "installed")
            config.write_bytes(b"changed settings")
            self.assertEqual(state(), "installed")
            app_file.write_bytes(b"tampered")
            self.assertEqual(state(), "repair-needed")
            app_file.unlink()
            self.assertEqual(state(), "repair-needed")


if __name__ == "__main__":
    unittest.main()
