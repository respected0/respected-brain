"""Public package entrypoints replace the retired source launchers."""
from __future__ import annotations
from pathlib import Path
import subprocess
import sys
import unittest
from unittest import mock
from respected_brain import cli
from tests.support.fakes import IntegrationFixture
from tests.support.files import snapshot

ROOT = Path(__file__).resolve().parents[2]


class RuntimeLayoutTest(IntegrationFixture, unittest.TestCase):
    def test_public_commands_preserve_selected_uuid_and_exit_status(self):
        for command in ("repair", "uninstall", "open"):
            with self.subTest(command=command), mock.patch.object(cli, "_dispatch", return_value=7) as dispatch:
                self.assertEqual(cli.main([command, "--vault-id", self.ctx.paths.vault_id]), 7)
                args = dispatch.call_args.args[0]
                self.assertEqual((args.command, args.vault_id), (command, self.ctx.paths.vault_id))

    def test_setup_accepts_explicit_vault(self):
        with mock.patch.object(cli, "_dispatch", return_value=4) as dispatch:
            self.assertEqual(cli.main(["setup", "--vault", str(self.vault)]), 4)
        args = dispatch.call_args.args[0]
        self.assertEqual(args.vault, self.vault)

    def test_importing_package_services_has_no_home_io_or_process_side_effect(self):
        probe = '''
import importlib, sys
from pathlib import Path
from unittest import mock
before = list(sys.path)
with mock.patch.object(Path, 'home', side_effect=AssertionError('home lookup')), mock.patch.object(Path, 'mkdir', side_effect=AssertionError('mkdir')), mock.patch('subprocess.run', side_effect=AssertionError('process')):
    importlib.import_module('respected_brain.' + sys.argv[1])
assert sys.path == before
'''
        for name in ("core.paths", "installation.setup", "installation.uninstall", "integrations.rendering"):
            with self.subTest(name=name):
                checked = subprocess.run([sys.executable, '-c', probe, name], cwd=ROOT,
                                         capture_output=True, text=True, timeout=30)
                self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)
                self.assertEqual(checked.stdout, '')

    def test_project_renderer_keeps_notes_and_technical_state_separate(self):
        from tests.support.render import render_project_integrations
        before = snapshot(self.root)
        output = render_project_integrations(self.ctx, self.profile)
        self.assertEqual(snapshot(self.root), before)
        self.assertEqual(len(output), 5)
        for value in output.values():
            self.assertIn(self.ctx.paths.vault_id.encode(), value)
            self.assertNotIn(b".py", value)

if __name__ == "__main__":
    unittest.main()
