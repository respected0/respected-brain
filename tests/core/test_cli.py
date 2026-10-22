"""The installed entry point and module select and dispatch the same services."""
from contextlib import redirect_stdout, redirect_stderr
from datetime import datetime
import io
import json
import os
from pathlib import Path
import subprocess
import sysconfig
import tempfile
import unittest
from unittest.mock import patch

from tests.support.files import make_context, run_cli, snapshot
from respectedbrain.cli import main


class FoundationCliTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.ctx = make_context(self.root)
        self.env = {**os.environ, "RESPECTED_APP_DIR": str(self.root / "app"), "RESPECTED_DATA_DIR": str(self.root / "data"), "PYTHONUTF8": "1"}

    def call(self, args):
        out, err = io.StringIO(), io.StringIO()
        with patch.dict(os.environ, self.env), redirect_stdout(out), redirect_stderr(err):
            code = main(args)
        return code, out.getvalue(), err.getvalue()

    def test_module_and_entrypoint_dispatch_identically(self):
        args = ["vault", "list"]
        module = run_cli(args, env=self.env, cwd=self.root)
        executable = Path(sysconfig.get_path("scripts")) / ("respectedbrain.exe" if os.name == "nt" else "respectedbrain")
        entry = subprocess.run([str(executable), *args], cwd=self.root, env=self.env, capture_output=True, text=True, encoding="utf-8", timeout=30)
        self.assertEqual(module.returncode, 0, module.stderr)
        self.assertEqual((module.returncode, module.stdout), (entry.returncode, entry.stdout))
        self.assertIn(self.ctx.paths.vault_id, module.stdout)

    def test_vault_selector_validation(self):
        before = snapshot(self.root)
        self.assertEqual(self.call(["compile", "--vault", str(self.root / "missing")])[0], 2)
        self.assertEqual(self.call(["compile", "--vault", str(self.ctx.paths.vault_root), "--vault-id", self.ctx.paths.vault_id])[0], 2)
        self.assertEqual(snapshot(self.root), before)

    def test_existing_features_have_one_dispatcher(self):
        with patch("respectedbrain.memory.compile.compile_memory", return_value=0) as compile_call:
            self.assertEqual(self.call(["compile", "--vault-id", self.ctx.paths.vault_id])[0], 0)
        self.assertEqual(compile_call.call_args.args[0].paths, self.ctx.paths)
        with patch("respectedbrain.briefing.service.run_if_due", return_value=1) as briefing_call:
            self.assertEqual(self.call(["briefing", "--vault-id", self.ctx.paths.vault_id])[0], 1)
        self.assertEqual(briefing_call.call_args.args[0].paths.vault_id, self.ctx.paths.vault_id)

    def test_hook_stdout_and_mcp_delegate_without_extra_text(self):
        with patch("respectedbrain.integrations.hooks.bridge.dispatch", return_value='{"hookSpecificOutput":{}}\n') as service, patch("sys.stdin", io.StringIO('{}')):
            code, out, err = self.call(["hook", "--vault-id", self.ctx.paths.vault_id, "--provider", "claude", "--event", "start", "--global-hook"])
        self.assertEqual((code, out, err), (0, '{"hookSpecificOutput":{}}\n', ""))
        self.assertEqual(service.call_args.kwargs["stdin"], '{}')
        self.assertEqual(service.call_args.kwargs["argv"], ["--global-hook"])
        with patch("respectedbrain.integrations.mcp.server.serve", return_value=0) as server:
            code, out, err = self.call(["mcp", "--vault-id", self.ctx.paths.vault_id])
        self.assertEqual((code, out, err), (0, "", ""))
        self.assertEqual(server.call_args.args[0].paths, self.ctx.paths)

    def test_discovery_is_explicit_and_configure_preserves_other_keys(self):
        before = snapshot(self.root)
        code, out, _ = self.call(["vault", "discover", str(self.ctx.paths.vault_root)])
        self.assertEqual(code, 0)
        self.assertEqual(out.strip(), str(self.ctx.paths.vault_root))
        self.assertEqual(snapshot(self.root), before)

    def test_config_reads_writes_and_refuses_with_the_shared_error_shape(self):
        code, out, _ = self.call(["config"])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["summary_provider"], "auto")
        code, out, _ = self.call(["config", "set", "summary_provider=codex", "briefing_time=07:15"])
        self.assertEqual((code, json.loads(out)), (0, {"summary_provider": "codex", "briefing_time": "07:15"}))
        self.assertEqual(json.loads(self.call(["config", "get", "summary_provider"])[1]), {"summary_provider": "codex"})
        config = json.loads((self.root / "data/config.json").read_text(encoding="utf-8"))
        self.assertEqual(config["preferences"]["summary_provider"], "codex")
        self.assertFalse(config["integrations"]["schedule"])
        for args in (["config", "set", "summary_provider=nope"], ["config", "set", "nope=1"], ["config", "get", "nope"], ["config", "set"]):
            code, out, _ = self.call(args)
            self.assertEqual(code, 2, args)
            self.assertEqual(set(json.loads(out)["error"]), {"code", "message", "hint"})

    def test_version_names_the_product(self):
        from respectedbrain import __version__
        self.assertEqual(self.call(["--version"])[1].strip(), f"respected-secondbrain {__version__}")

    def test_flush_child_command_uses_selected_context_and_keeps_unmanaged_input(self):
        payload = self.root / "input.json"
        transcript = self.root / "turn.jsonl"
        transcript.write_text('{}\n', encoding="utf-8")
        payload.write_text(json.dumps({"session_id": "same", "transcript_path": str(transcript)}), encoding="utf-8")
        with patch("respectedbrain.memory.flush.flush_transcript", return_value=0) as service:
            self.assertEqual(self.call(["flush", "--vault-id", self.ctx.paths.vault_id, "--hook-input", str(payload), "--reason", "turn"])[0], 0)
        self.assertEqual(service.call_args.args[0].paths.vault_id, self.ctx.paths.vault_id)
        self.assertEqual(service.call_args.kwargs["transcript"], transcript)
        self.assertTrue(payload.exists())

    def test_setup_takes_settings_through_set_and_refuses_unknown_ones(self):
        from respectedbrain.installation.transaction import OperationResult
        vault = str(self.ctx.paths.vault_root)
        with patch("respectedbrain.installation.setup.setup", return_value=OperationResult(False, "test", ("fault",))) as service:
            self.assertEqual(self.call(["setup", "--vault", vault, "--set", "user_name=Ada", "--set", "integrations.mcp=true",
                                        "--set", "integrations.clients=claude,codex"])[0], 1)
        self.assertEqual(service.call_args.args[1], self.ctx.paths.vault_root)
        self.assertEqual(service.call_args.kwargs["values"], {"user_name": "Ada", "integrations.mcp": True, "integrations.clients": "claude,codex"})
        with patch("respectedbrain.installation.setup.setup") as service:
            for retired in (["--user-name", "Ada"], ["--clients", "claude"], ["--package", "x"], ["--set", "integrations.mcp=yes"]):
                self.assertEqual(self.call(["setup", "--vault", vault, *retired])[0], 2, retired)
        service.assert_not_called()

    def test_uninstall_keeps_data_unless_purged(self):
        from respectedbrain.installation.transaction import OperationResult
        for flags, purge in (([], False), (["--purge"], True)):
            with patch('respectedbrain.installation.uninstall.uninstall', return_value=OperationResult(True, "test", ())) as service:
                self.assertEqual(self.call(['uninstall', '--vault-id', self.ctx.paths.vault_id, *flags])[0], 0)
            self.assertEqual(service.call_args.kwargs['purge_data'], purge)
