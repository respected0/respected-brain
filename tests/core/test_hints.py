import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from respected_brain import cli, hints


class HintsTest(unittest.TestCase):
    def test_without_the_hub_only_the_product_command_is_named(self):
        with mock.patch.object(hints, "hub_installed", return_value=False):
            text = hints.hint("Hub'dan açın", "respected-brain semantic enable")
        self.assertEqual(text, "Şu komutu çalıştırın: respected-brain semantic enable")

    def test_with_the_hub_both_ways_are_named(self):
        with mock.patch.object(hints, "hub_installed", return_value=True):
            text = hints.hint("Hub'dan açın", "respected-brain semantic enable")
        self.assertEqual(text, "Hub'dan açın; ya da: respected-brain semantic enable")

    def test_hub_is_detected_next_to_the_product_folders(self):
        with tempfile.TemporaryDirectory() as name:
            respected = Path(name) / "Respected"
            exe = respected / "RespectedHub/app/respected-hub.exe"
            exe.parent.mkdir(parents=True)
            exe.write_bytes(b"")
            roots = mock.Mock(data_root=respected / "RespectedBrain/data")
            with mock.patch("respected_brain.bootstrap.application_roots", return_value=roots):
                self.assertTrue(hints.hub_installed())
                exe.unlink()
                self.assertFalse(hints.hub_installed())


class SemanticCommandTest(unittest.TestCase):
    def test_status_without_a_vault_is_a_usage_error_with_the_shared_shape(self):
        with tempfile.TemporaryDirectory() as name, mock.patch.dict(os.environ, {"RESPECTED_APP_DIR": name + "/app", "RESPECTED_DATA_DIR": name + "/data"}):
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = cli.main(["semantic", "status"])
        self.assertEqual(code, 2)
        self.assertEqual(set(json.loads(out.getvalue())["error"]), {"code", "message", "hint"})


if __name__ == "__main__":
    unittest.main()
