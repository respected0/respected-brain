"""Running executables queue verified temporary helpers rather than overwrite themselves."""
from pathlib import Path
import json
import tempfile
import unittest
from unittest import mock
from unittest.mock import patch
from tests.support.files import make_context, snapshot
from respectedbrain.core.errors import OwnershipConflict
from respectedbrain.installation import deferred
from respectedbrain.installation.ownership import digest
from respectedbrain.installation.transaction import OperationResult
from tests.support.packages import seed_package


class FoundationDeferredTest(unittest.TestCase):
    def test_active_executable_uses_os_temp_and_reports_pending(self):
        from respectedbrain.installation.deferred import defer_operation
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            ctx = make_context(root)
            seed_package(ctx.paths.app_root)
            new = seed_package(root / "new", content=b"MZ-new")
            before = snapshot(ctx.paths.app_root)
            with patch("respectedbrain.installation.deferred.sys.platform", "win32"), patch("respectedbrain.installation.deferred.sys.frozen", True, create=True), patch("respectedbrain.installation.deferred.sys.executable", str(ctx.paths.app_root / "respectedbrain.exe")), patch("respectedbrain.installation.deferred.subprocess.Popen") as process:
                result = defer_operation(ctx, mode="update", package=new, require_provenance=False)
            self.assertTrue(result.pending)
            self.assertFalse(result.success)
            helper = Path(process.call_args.args[0][0])
            self.assertTrue(helper.is_relative_to(Path(tempfile.gettempdir()).resolve()))
            self.assertFalse(helper.is_relative_to(ctx.paths.data_root))
            self.assertEqual(snapshot(ctx.paths.app_root), before)
            self.assertEqual(helper.read_bytes(), b"MZ-fixture")
            import shutil
            shutil.rmtree(helper.parent)

    def test_helper_canonicalizes_its_owned_os_temp_allocation(self):
        from respectedbrain.installation import deferred
        from tests.support.fakes import owned_temp_alias
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            ctx = make_context(root)
            seed_package(ctx.paths.app_root)
            package = seed_package(root / 'new', content=b'MZ-new')
            before = snapshot(ctx.paths.app_root)
            with owned_temp_alias(self, root) as (alias, allocated):
                (allocated / 'activation').mkdir()
                with patch.object(deferred.sys, 'platform', 'win32'), patch.object(deferred.sys, 'frozen', True, create=True), patch.object(deferred.sys, 'executable', str(ctx.paths.app_root / 'respectedbrain.exe')), patch.object(deferred.tempfile, 'mkdtemp', return_value=str(alias / 'activation')), patch.object(deferred.subprocess, 'Popen') as process:
                    result = deferred.defer_operation(ctx, mode='update', package=package, require_provenance=False)
                self.assertTrue(result.pending)
                helper = Path(process.call_args.args[0][0])
                self.assertEqual(helper, allocated / 'activation/respectedbrain.exe')
                self.assertEqual(helper.read_bytes(), b'MZ-fixture')
                self.assertEqual(snapshot(ctx.paths.app_root), before)

    def test_tampered_request_stops_before_any_activation(self):
        from respectedbrain.installation.deferred import resume_operation
        from respectedbrain.core.errors import OwnershipConflict
        with tempfile.TemporaryDirectory() as temporary:
            request = Path(temporary).resolve() / "request.json"
            request.write_text('{}', encoding="utf-8")
            with self.assertRaises(OwnershipConflict):
                resume_operation(request, expected_hash="0" * 64)


def frozen_launcher(ctx):
    """Make deferred.py believe the running process is the installed frozen Windows launcher."""
    stack = mock.patch.multiple(deferred.sys, platform="win32", frozen=True, create=True,
                                executable=str(ctx.paths.app_root / "respectedbrain.exe"))
    return stack


class DeferOperationGuardTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.ctx = make_context(Path(temporary.name).resolve())
        seed_package(self.ctx.paths.app_root)

    def test_source_runs_are_never_deferred(self):
        self.assertIsNone(deferred.defer_operation(self.ctx, mode="uninstall", require_provenance=False))

    def test_only_activation_and_removal_defer(self):
        with frozen_launcher(self.ctx), self.assertRaises(ValueError):
            deferred.defer_operation(self.ctx, mode="repair", require_provenance=False)

    def test_failed_launch_removes_the_temporary_helper(self):
        created = []
        real = tempfile.mkdtemp
        with frozen_launcher(self.ctx),                 patch.object(deferred.tempfile, "mkdtemp", side_effect=lambda **kw: created.append(real(**kw)) or created[-1]),                 patch.object(deferred.subprocess, "Popen", side_effect=OSError("cannot start")):
            with self.assertRaises(OSError):
                deferred.defer_operation(self.ctx, mode="uninstall", require_provenance=False)
        self.assertEqual(len(created), 1)
        self.assertFalse(Path(created[0]).exists())


class WaitParentTest(unittest.TestCase):
    def kernel(self, *, handle, waited=0, error=0):
        kernel = mock.MagicMock()
        kernel.OpenProcess.return_value = handle
        kernel.WaitForSingleObject.return_value = waited
        stack = [mock.patch.object(deferred.sys, "platform", "win32"),
                 mock.patch.object(deferred.ctypes, "WinDLL", return_value=kernel, create=True),
                 mock.patch.object(deferred.ctypes, "get_last_error", return_value=error, create=True)]
        for patcher in stack:
            patcher.start()
            self.addCleanup(patcher.stop)
        return kernel

    def test_other_platforms_cannot_run_the_helper(self):
        with patch.object(deferred.sys, "platform", "linux"), self.assertRaises(ValueError):
            deferred._wait_parent(1)

    def test_exited_parent_needs_no_wait(self):
        kernel = self.kernel(handle=0, error=87)
        deferred._wait_parent(4242)
        kernel.WaitForSingleObject.assert_not_called()

    def test_unopenable_parent_stops_the_activation(self):
        self.kernel(handle=0, error=5)
        with self.assertRaises(OSError):
            deferred._wait_parent(4242)

    def test_parent_that_exits_releases_its_handle(self):
        kernel = self.kernel(handle=77, waited=0)
        deferred._wait_parent(4242)
        kernel.CloseHandle.assert_called_once_with(77)

    def test_parent_that_never_exits_cancels_the_activation_and_releases_its_handle(self):
        kernel = self.kernel(handle=77, waited=258)
        with self.assertRaises(OSError):
            deferred._wait_parent(4242)
        kernel.CloseHandle.assert_called_once_with(77)


class ResumeOperationTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.ctx = make_context(self.root)
        self.helper = Path(tempfile.mkdtemp(prefix="respected-activation-test-")).resolve()
        self.addCleanup(lambda: __import__("shutil").rmtree(self.helper, ignore_errors=True))
        seed_package(self.helper)
        patch.object(deferred, "_wait_parent").start()
        self.addCleanup(patch.stopall)

    def request(self, receipt=None, **overrides):
        paths = self.ctx.paths
        document = {"schema_version": 3, "parent_pid": 1, "mode": "uninstall", "app_root": str(paths.app_root),
                    "data_root": str(paths.data_root), "vault": str(paths.vault_root), "vault_id": paths.vault_id,
                    "package": None, "purge_data": False,
                    "receipt": str(receipt or paths.data_root / "backups" / "deferred-1" / "result.json"), **overrides}
        path = self.helper / "request.json"
        path.write_text(json.dumps(document), encoding="utf-8")
        return path

    def resume(self, path):
        return deferred.resume_operation(path, expected_hash=digest(path), require_provenance=False)

    def test_helper_outside_os_temp_storage_is_refused(self):
        with patch.object(deferred.tempfile, "gettempdir", return_value=str(self.root)), self.assertRaises(OwnershipConflict):
            self.resume(self.request())

    def test_unknown_schema_or_mode_is_refused(self):
        for override in ({"schema_version": 2}, {"mode": "repair"}):
            with self.subTest(override=override), self.assertRaises(OwnershipConflict):
                self.resume(self.request(**override))

    def test_receipt_outside_the_deferred_backup_area_is_refused(self):
        for receipt in (self.root / "elsewhere" / "result.json", self.ctx.paths.data_root / "backups" / "plain" / "result.json"):
            with self.subTest(receipt=receipt), self.assertRaises(OwnershipConflict):
                self.resume(self.request(receipt=receipt))

    def test_uninstall_result_is_written_and_sets_the_exit_code(self):
        for success, code in ((True, 0), (False, 1)):
            with self.subTest(success=success):
                path = self.request()
                with patch("respectedbrain.installation.uninstall.uninstall", return_value=OperationResult(success, "op", ())) as run:
                    self.assertEqual(self.resume(path), code)
                self.assertFalse(run.call_args.kwargs["purge_data"])
                receipt = json.loads((self.ctx.paths.data_root / "backups" / "deferred-1" / "result.json").read_text(encoding="utf-8"))
                self.assertEqual(receipt["success"], success)

    def test_update_hands_the_staged_package_to_the_engine(self):
        package = seed_package(self.root / "new", content=b"MZ-new")
        path = self.request(mode="update", package=str(package))
        with patch("respectedbrain.installation.update.update", return_value=OperationResult(True, "op", ())) as run:
            self.assertEqual(self.resume(path), 0)
        self.assertEqual(run.call_args.kwargs["package"], package)

