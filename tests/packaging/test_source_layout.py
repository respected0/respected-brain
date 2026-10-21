"""Guard the single source tree and the native release entrypoint contract."""
from pathlib import Path
import importlib.util
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]


class SourceCleanupTest(unittest.TestCase):
    def test_macos_smoke_uses_app_bundle_for_source_and_install_destination(self):
        spec = importlib.util.spec_from_file_location('platform_smoke', ROOT / 'tests/native/smoke/platform_smoke.py')
        tool = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(tool)
        root = Path('/isolated-smoke')
        with mock.patch.object(tool.sys, 'platform', 'darwin'):
            self.assertEqual(tool.distribution_name(), 'RespectedBrain.app')
            self.assertEqual(tool.workspace_paths(root)[1], root / 'RespectedBrain.app')
        with mock.patch.object(tool.sys, 'platform', 'linux'):
            self.assertEqual(tool.distribution_name(), 'RespectedBrain')
            self.assertEqual(tool.workspace_paths(root)[1], root / 'app')

    def test_retired_source_entrypoints_are_absent(self):
        for name in ("runtime", "installer", "template", "setup.py", "setup", "setup.command"):
            with self.subTest(name=name):
                self.assertFalse((ROOT / name).exists(), f"Retired source remains: {name}")


if __name__ == "__main__":
    unittest.main()
