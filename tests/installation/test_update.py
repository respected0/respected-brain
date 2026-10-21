"""Update preserves the public package CLI contract."""
from pathlib import Path
import unittest
from unittest import mock
from respectedbrain.installation.transaction import OperationResult
from respectedbrain import cli
from tests.support.fakes import IntegrationFixture

class TestUpdateCli(IntegrationFixture,unittest.TestCase):
    def test_update_requires_explicit_verified_package_without_vault_discovery(self):
        with mock.patch("respectedbrain.cli._dispatch",side_effect=AssertionError("mutation")):
            self.assertEqual(cli.main(["update","--vault-id",self.ctx.paths.vault_id]),2)

    def test_update_main_dispatches_selected_uuid_and_package_once(self):
        from respectedbrain import cli
        backend=mock.Mock()
        with mock.patch.object(cli,"bootstrap",return_value=self.ctx),mock.patch("respectedbrain.integrations.backend.NativeBackend",return_value=backend),mock.patch("respectedbrain.installation.deferred.defer_operation",return_value=None),mock.patch("respectedbrain.installation.update.update",return_value=OperationResult(True,"test",())) as update:
            code=cli.main(["update","--vault-id",self.ctx.paths.vault_id,"--package",str(self.root / "package")])
        self.assertEqual(code,0)
        update.assert_called_once_with(self.ctx,package=(self.root / "package").resolve(),backend=backend,require_provenance=None)

    def test_allow_unattested_is_explicit_and_only_then_relaxes_provenance(self):
        from respectedbrain import cli
        backend=mock.Mock()
        with mock.patch.object(cli,"bootstrap",return_value=self.ctx),mock.patch("respectedbrain.integrations.backend.NativeBackend",return_value=backend),mock.patch("respectedbrain.installation.deferred.defer_operation",return_value=None) as defer,mock.patch("respectedbrain.installation.update.update",return_value=OperationResult(True,"test",())) as update:
            cli.main(["update","--vault-id",self.ctx.paths.vault_id,"--package",str(self.root / "package"),"--allow-unattested"])
        self.assertIs(update.call_args.kwargs["require_provenance"],False)
        self.assertIs(defer.call_args.kwargs["require_provenance"],False)

    def test_update_failure_exit_status_is_not_rewritten_to_success(self):
        from respectedbrain import cli
        with mock.patch.object(cli,"bootstrap",return_value=self.ctx),mock.patch("respectedbrain.integrations.backend.NativeBackend"),mock.patch("respectedbrain.installation.deferred.defer_operation",return_value=None),mock.patch("respectedbrain.installation.update.update",return_value=OperationResult(False,"test",("failure",))):
            code=cli.main(["update","--vault-id",self.ctx.paths.vault_id,"--package",str(self.root / "package")])
        self.assertEqual(code,1)

class AutoUpdaterTest(unittest.TestCase):
    def test_explicit_verified_package_update_preserves_exit_status(self):
        identity = "93e9e921-3334-4a6a-a381-1d4c42a9d405"
        with mock.patch.object(cli, "_dispatch", return_value=6) as dispatch:
            self.assertEqual(cli.main(["update", "--vault-id", identity, "--package", "/explicit/package"]), 6)
        args = dispatch.call_args.args[0]
        self.assertEqual((args.command, args.vault_id, args.package), ("update", identity, Path("/explicit/package")))

    def test_old_force_check_options_are_not_silently_applied(self):
        with mock.patch.object(cli, "_dispatch", side_effect=AssertionError("write")):
            self.assertEqual(cli.main(["update", "--force", "--check"]), 2)


if __name__=="__main__":
    unittest.main()
